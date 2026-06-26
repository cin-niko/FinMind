---
id: SPEC-FEAT-003
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs:
  - docs/adr/0005-phase-003-m1-m2-chat-milestones.md
  - docs/adr/0006-shared-evidence-lineage-tables.md
---

# Feature Specification: Evidence-Backed Chat

## Summary

Deliver a chat tab where authenticated internal users ask supported VN stock
finance questions. Chat must reuse the same evidence, citations, chart
artifacts, freshness metadata, and execution records established by the workflow
platform. While Phase 002 market-data population is pending, M1 answers use
real-time retrieval tools as the source of truth and cite the tool output
instead of requiring rows to exist in `vn_prices_daily`.

V1 user-facing market scope is VN stocks only (VN100 universe), inherited
from `../002-data-operations/` after the 2026-06-25 VN-only scope-down.
Roadmap markets (US stocks, XAUUSD, SJC gold, BTC) return clear out-of-scope
behavior.

## Milestones

Phase 003 ships in two sequential milestones so the chat surface itself can
land before the fundamentals data layer:

### Milestone 003.M1 — Tool-Grounded Workflow/Chatflow (ship first)

Chat/workflow orchestration over real-time retrieval tools for supported VN
stock questions, grounded through the existing evidence/citation contracts.
Supported answer surfaces include quote/status answers, tool-cited chart/table
summaries, freshness-aware limitations, and lightweight price-derived metrics
when the retrieved tool payload contains enough data.

M1 does NOT require a populated market database. Its goal is to prove the
end-to-end evidence-grounding loop — chat/workflow → call retrieval tool → cite
tool result → render chart/table artifact → freshness/source banner — while
Phase 002 market-data ingestion remains pending.

### Milestone 003.M2 — Fundamentals Layer + Fundamentals-Cited Chat

Add a fundamentals data layer above Phase 002's price ingestion (new
typed tables for company identity, financial facts, and earnings;
vnstock-derived adapter using the existing source connector contract).
Extend chat workflows so material claims about fundamentals (revenue
growth, earnings beats, ratios, dividend history) cite the new typed
tables through the same evidence/citation contracts used for prices.

M2 is a separate spec milestone with its own data-model and contracts
work. It MUST NOT block M1. Concrete fundamentals schema and adapter
work is deferred until M1 ships and at least three concrete chat use
cases drive the requirements.

Object storage (S3/MinIO) for large documents/reports is NOT introduced
in M1 or M2 unless a concrete chat workflow needs it; current
`source_documents` and `artifacts` JSONB storage covers M1 scope.

## User Scenarios & Testing

### User Story 1 - Ask Evidence-Backed Questions (Priority: P1)

An authenticated internal user asks open-ended finance research questions in chat where role-based agents coordinate over shared platform contracts.

**Independent Test**: Ask a supported VN stock or gold question and verify that the answer includes citations, freshness metadata, role-agent execution status, inline visualization when useful, and no unsupported claims beyond available evidence.

Acceptance scenarios:

1. Given the user is logged in and asks a supported finance question, when chat orchestration completes, then the answer includes cited evidence, freshness metadata, and execution artifacts consistent with the workflow surface.
2. Given the user asks a question outside V1 market scope, when the chat run completes, then the system states the scope limitation and avoids fabricating unsupported analysis.
3. Given a chat answer uses a chart or derived artifact, when the user inspects it, then the artifact is traceable to canonical data and citations.
4. Given a chat task benefits from computed analysis or visualization, when the system produces an inline artifact, then the artifact is linked to its inputs, execution record, and evidence.

## Functional Requirements

Each FR below is tagged with its target milestone (`[M1]`, `[M2]`, or `[M1+M2]`).
M1 FRs MUST be satisfied before M2 work begins.

- **FR-007** `[M1]`: System MUST provide a chat tab where generic role-based agents answer supported open-ended finance questions using the same evidence, citations, charts, inline visualizations, and execution records as fixed workflows. M1 scope covers price/quote-derived questions from real-time retrieval tool outputs while Phase 002 market data is pending.
- **FR-013** `[M1+M2]`: Every user-facing chat answer MUST expose citations and freshness metadata for material claims. M1 citations cover retrieval tool outputs; M2 extends citations to fundamentals records and source documents.
- **FR-014** `[M1]`: System MUST generate and display chart/table artifacts for chat outputs when the retrieval tool returns enough structured price/quote history to render them; otherwise it MUST state the tool-data limitation.
- **FR-015** `[M1+M2]`: Chat MUST support inline visualization artifacts for complex tasks where a chart, table, or computed result materially improves user understanding. M1 covers tool-derived quote/price tables/charts; M2 adds fundamentals-derived tables (e.g. quarterly statement summaries, ratio comparisons).
- **FR-016** `[M1]`: System MUST record execution logs for chat runs, tool calls, generated artifacts, failures, and user-visible output status.
- **FR-017** `[M1]`: System MUST distinguish workflow agents from generic role agents while preserving shared lower-layer contracts for data access, evidence, citations, charts, inline artifacts, and execution records.
- **FR-018** `[M1]`: System MUST expose result views where users can inspect completed chat outputs, citations, charts, freshness, and execution status after the original run.
- **FR-019** `[M1]`: System MUST show clear out-of-scope behavior for unsupported markets, unsupported instruments (outside the VN100 universe), missing data, stale data, and unavailable citations. References to tickers outside the VN100 universe MUST return out-of-scope without attempting lazy ingestion.
- **FR-030** `[M1]`: Retrieval tools used by workflow/chatflow MUST produce a structured evidence payload containing source name, retrieval timestamp, requested symbol/question, normalized fields used in the answer, and any warning/error state. Raw scraped/provider payload dumps MUST NOT be shown directly to users.
- **FR-031** `[M1]`: When a retrieval tool fails, rate-limits, or cannot return enough structured data, chat/workflow output MUST surface the failure as a cited unavailable-data state and MUST NOT fall back to demo market fixtures.
- **FR-020** `[M1]`: System MUST show users evidence, citations, role-agent stages, and tool or artifact status while retaining raw agent reasoning internally and excluding it from user-facing chat views.
- **FR-026** `[M2]`: Milestone M2 MUST introduce a fundamentals data layer using the Phase 002 source connector contract, with typed PostgreSQL tables for company identity, financial facts (income statement, balance sheet, cash flow line items as-reported and restated), and earnings events. Schema design MUST be driven by at least three concrete chat use cases recorded in M2's research artifact rather than imported wholesale from external reference architectures.
- **FR-027** `[M2]`: Fundamentals ingestion MUST share the canonical idempotent ingestion path (planner → source adapter → store_writer → upsert), MUST honor the same overlap guard and `ingestion_jobs` lineage as price ingestion, and MUST be exposed in admin freshness output alongside price datasets.
- **FR-028** `[M2]`: Fundamentals records MUST be citable through the existing `evidence_objects` / `citations` contracts. Chat claims referencing fundamentals MUST link to the underlying typed records with point-in-time semantics (fiscal period, filing/restatement timestamp, currency) preserved.
- **FR-029** `[M2]`: Fundamentals freshness MUST use a fiscal-period-aware rule distinct from price freshness: a record is `fresh` when the latest available fiscal period for the instrument matches the expected most recent period for its reporting calendar, `stale` when the expected period has passed without an update, `missing` when no records exist, and `failed` when the latest fundamentals ingestion job failed.

## Key Entities

M1 entities:

- Chat Session
- Role Agent
- Execution Run
- Evidence Object
- Citation
- Inline Visualization Artifact
- Chart Artifact
- Execution Log

M2 entities (added in milestone 003.M2):

- Company (legal entity, listings, classifications)
- Financial Fact (normalized statement line items, as-reported and restated, point-in-time)
- Earnings Event (announced EPS, surprises, fiscal period, announcement date)
- Fundamentals Ingestion Job (specialization of `IngestionJob` with fiscal-period scope)

See `../system/state-model.md` for canonical entity definitions. M2 entities
will be added to the system state model when milestone M2 is specified.

## Edge Cases

- Supported data exists but is stale: chat outputs display freshness warnings.
- Real-time retrieval fails, rate-limits, or returns partial data: chat outputs show the unavailable or partial-data state and avoid unsupported analysis.
- A chat run partially completes: the result distinguishes completed sections, failed sections, and unavailable artifacts.
- Citations are unavailable for a generated claim: the claim is omitted, qualified, or marked unsupported.
- Unsupported US stock, gold (XAUUSD/SJC), or BTC requests return a clear V1 scope limitation; tickers outside the pre-seeded VN100 universe are also out-of-scope and MUST NOT trigger lazy ingestion or instrument creation.
- M1 receives a question requiring fundamentals (e.g. earnings, revenue growth, ratios): chat answers with a clear capability limitation pointing to M2, never with a fabricated number.
- M2 fundamentals coverage gap (e.g. quarterly filing not yet published): chat surfaces the missing period explicitly with freshness metadata rather than answering against a stale prior period without qualification.

## Success Criteria

M1:

- **SC-003** `[M1]`: 100% of user-facing material claims in M1 chat outputs include at least one citation or are explicitly marked unsupported or unavailable.
- **SC-006** `[M1]`: At least 95% of supported M1 chat result views show retrieval timestamp/freshness metadata for every cited tool output.
- **SC-007** `[M1]`: Users can identify stale, missing, failed, or out-of-scope data conditions from the chat UI without reading server logs.
- **SC-009** `[M1]`: At least one approved M1 chat scenario produces an inline visualization or computed artifact that is inspectable and tied to cited price inputs.

M2:

- **SC-010** `[M2]`: At least three approved chat use cases driving the fundamentals schema are documented before any M2 implementation work begins.
- **SC-011** `[M2]`: 100% of fundamentals-derived material claims in M2 chat outputs cite the underlying typed fundamentals records with fiscal-period and as-reported/restated qualifiers preserved.
- **SC-012** `[M2]`: Fundamentals freshness rows appear alongside price freshness in admin and chat surfaces using the fiscal-period-aware rule.

## Out Of Scope

- Chat-specific data stores that duplicate workflow evidence/freshness logic.
- US stocks, gold (XAUUSD and SJC), and BTC as V1 supported markets.
- Open on-demand instrument creation outside the pre-seeded VN100 universe.
- Object storage (S3/MinIO) for large documents/reports in M1; revisit in M2 only if a concrete use case requires it.
- External plugin adapter; see `../004-extension-hardening/`.
- Analyst estimates (forward EPS consensus), holders/ownership, and dividend history in M2; these may be added in a later phase after the core M2 fundamentals layer ships.
