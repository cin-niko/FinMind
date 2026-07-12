---
id: SPEC-FEAT-003-PLAN
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Implementation Plan: VN And Gold Dataflows And Workflows

## Summary

Implement the next runnable market scope after the Phase 02 workflow foundation:
gold dataflows plus mature fixed workflows for VN stocks and gold. This phase
adopts the unfinished composite-workflow, validation, history, and delivery work
from `../002-workflow/`. It does not implement flexible chatflow, which remains
owned by `../004-agentic-chatflow/`.

## Technical Context

- Foundation: Phase 02 supplies the shared runtime, collection-first dataflow
  boundary, deterministic record rendering, citation allowlist, workflow SSE
  events, artifact contract, and run-store foundation.
- Active market boundary: enabled workflow inputs are `VN_STOCK` and `GOLD`.
- Gold source: `XAUUSD` is the sole supported Gold benchmark. Twelve Data
  supplies OHLC evidence through the dataflow connector contract; timestamps
  normalize to UTC and absent volume remains absent.
- Runtime: retain the shared LangChain/LiteLLM-backed workflow runtime and its
  request-scoped SSE behavior. New workflow code must not bypass the dataflow,
  citation, grounding, or bounded-offload boundaries.
- Storage: reuse the PostgreSQL run store and persisted citation snapshots.
  Gold source data follows the same canonical record and evidence-snapshot model.
- UI: extend the existing workflow catalog, validation, transcript result,
  history, artifact, citation-panel, and server-persisted Vietnamese/English
  preference surfaces. On first authenticated use, persist the supported
  browser language or English as the default. Do not activate production
  chatflow UI behavior in this phase.

## Constitution Check

- Specs before code: Phase 03 owns the feature behavior, API extension, and
  validation scenarios before implementation begins.
- Evidence and safety: gold and VN claims require citations or explicit
  unsupported/unavailable status; raw reasoning and provider payloads remain
  internal.
- Human control: workflows provide research support only and refuse trading,
  broker, and order actions.
- Scope: enabled inputs remain VN stocks and `XAUUSD`. Other assets are rejected
  or shown unavailable. Technical outputs are analysis-only and never produce
  trading signals, verdicts, entry/exit instructions, or target prices.
- Shared contracts: market enum expansion and active-scope rules live in
  `../system/state-model.md` and `../system/runtime-config-security.md`.

Gate result: planning is ready for implementation only after Twelve Data source
rights and contract validation, the VN news search-domain allowlist and source
handling, valuation methodology, and language-preference contract validation
tasks are complete.

## Architecture And Ownership

- `src/finmind_agents/dataflows/`: gold connector selection, normalization,
  freshness, source-status handling, and deterministic gold evidence records.
- `src/finmind_agents/workflows/`: VN stock brief composition, market-specific
  catalog metadata, input validation, and workflow execution assembly. Existing
  VN technical and fundamental workflow runtime is refined through its skill,
  evidence, output, language, and safety contracts rather than rebuilt.
- `src/finmind_api/`: workflow/catalog/run/citation delivery contracts and
  persisted-run queries.
- `src/finmind_ui/`: market-aware catalog inputs, validation states, stage
  visibility, history reinspection, artifacts, and citations.
- `tests/`: gold collection, bounded market rejection, composed VN workflows,
  persisted-run reinspection, and evidence/safety regressions.

## Delivery Sequence

1. Validate Twelve Data rights, limits, Gold OHLC schema, freshness expectation,
   and provider-failure behavior for `XAUUSD`.
2. Extend shared dataflow and market validation contracts for `GOLD`.
3. Build gold evidence collection and its deterministic records before any gold
   workflow can generate claims.
4. Refine the existing VN technical and fundamental workflows, then deliver new
   Gold technical analysis, VN news digest, VN valuation, and VN stock-brief
   workflows with bounded content and visible partial and unavailable states.
5. Deliver the server-persisted Vietnamese/English web preference and capture
   it in workflow runs without altering evidence fields.
6. Complete validation, run-history, citation reinspection, safety, risk, and
   quickstart verification across both markets.

## Deferred Scope

- Flexible production Q&A, conversations, chat-specific persistence, and
  chatflow streaming: `../004-agentic-chatflow/`.
- Out-of-scope asset coverage, broker actions, ingestion administration, and
  scheduled backfill.

## Design Artifacts

- Research decisions: `research.md`
- Feature-owned model usage: `data-model.md`
- Workflow and dataflow API contract: `contracts/workflow-contract.md`
- Validation guide: `quickstart.md`
