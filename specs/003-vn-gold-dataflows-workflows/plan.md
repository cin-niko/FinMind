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
  events, artifact contract, and persisted citation-snapshot foundation. Phase
  03 migrates workflow persistence from the Phase 02 run store to
  conversation-owned responses, citations, and artifacts without a market-
  specific citation or reproducibility layer.
- Active market boundary: enabled workflow inputs are `VN_STOCK` and `GOLD`.
- Gold source: `XAUUSD` is the sole supported Gold benchmark. The configured
  Gold connector fetches and upserts one daily OHLC price series per
  workflow-created conversation using the fullest history returned within its
  supported limit; timestamps normalize to UTC and absent volume remains absent.
  It retries a transient collection failure at most twice, then fails safely
  without a cached or fallback source. Multiple timeframes are deferred.
- VN news source: a configured web-search provider searches an application-
  maintained publisher-domain allowlist and returns article sources with URL,
  title, publication time, and provider-delivered content. The workflow consumes
  normalized source documents, never raw search or page payloads. Provider
  selection, exact source schema, rights, and retention are planning decisions.
- Runtime: retain the shared LangChain/LiteLLM-backed workflow runtime and its
  request-scoped SSE behavior. New workflow code must not bypass the dataflow,
  citation, grounding, or bounded-offload boundaries.
- VN valuation: use the Phase 03 sector-method baseline from
  `equity-research-vn/vn-valuation-engine/SKILL.md`, subject to FinMind's
  research-only safety contract. The implementation must derive valuation values
  deterministically from cited normalized inputs; it must not carry over the
  methodology source's target-price or buy/sell output.
- Storage: replace the PostgreSQL run store with a conversation store. Creating
  a workflow-created conversation persists workflow metadata before execution.
  A conversation adapter maps the workflow result to its first assistant message
  and stores citations and artifacts under that message. Deleting a conversation
  cascades to messages and their children but not shared Gold/VN canonical
  price-series data.
- UI: extend the existing workflow catalog, validation, transcript result,
  conversation history, artifact, citation-panel, and server-persisted
  language-selection surfaces. Starting a workflow always opens a new
  conversation; a conversation adapter maps its result into the first assistant
  message. Offer Auto-detect,
  English, and Vietnamese; Auto-detect is the
  default and resolves browser language for the current session. The UI sends
  only resolved `en` or `vi` with each workflow submission. The backend
  validates and captures it, and the workflow's LLM system-prompt template adds
  `Language: Respond in the {language} language`. Gold technical analysis is a
  direct-run XAUUSD card with no market, symbol, or instrument form. Do not
  activate production chatflow UI behavior in this phase.

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

Gate result: planning is ready for implementation only after configured Gold-
source rights and contract validation, the VN web-search-provider and source-
content contract decision, valuation evidence-input validation, and language-
preference contract validation tasks are complete.

## Architecture And Ownership

- `src/finmind_agents/dataflows/`: gold connector selection, normalization, UTC
  market/collection timestamp preservation, source-status handling, and
  deterministic gold evidence records.
- `src/finmind_agents/workflows/`: VN stock brief composition, market-specific
  catalog metadata, input validation, and workflow execution assembly. Existing
  VN technical and fundamental workflow runtime is refined through its skill,
  evidence, output, language, and safety contracts rather than rebuilt.
- `src/finmind_api/`: workflow/catalog/conversation/citation delivery contracts
  and owner-authorized conversation queries and deletion.
- `src/finmind_ui/`: market-aware catalog inputs, validation states, stage
  visibility, conversation history and deletion, artifacts, and citations.
- `tests/`: deterministic mocked/fixture-based coverage for gold collection,
  bounded market rejection, composed VN workflows, persisted-conversation
  ownership/deletion/reinspection, and evidence/safety regressions. Live-provider
  validation is separately recorded and never a test-suite dependency.

## Delivery Sequence

1. Validate the configured Gold source's rights, limits, daily OHLC schema,
  maximum returned history, timestamp provenance, and provider-failure behavior
  for `XAUUSD`, including any required attribution before the provider is
  enabled.
2. Extend shared dataflow and market validation contracts for `GOLD`.
3. Build gold evidence collection and its deterministic records before any gold
   workflow can generate claims.
4. Refine the existing VN technical and fundamental workflows, then deliver new
  Gold technical analysis, VN news digest, VN valuation, and VN stock-brief
  workflows with bounded content and visible field-level unavailable markers.
  Align conversation workflow metadata to use only successful or failed terminal
  statuses; a rendered unavailable field alone does not change a safely
  completed conversation.
5. Add 120-second workflow timeout handling, at most two retries for transient
  provider collection failures, continued execution after browser disconnect,
  and startup reconciliation that marks interrupted queued/running conversations
  failed.
  Do not add cancellation, idempotency, queue, concurrency limits, or resume
  behavior in this phase.
6. Deliver the server-persisted Vietnamese/English web preference and capture
  it in workflow-created conversations without altering evidence fields.
7. Complete validation, conversation-history ownership/deletion, citation
  reinspection, safety, risk, and
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
