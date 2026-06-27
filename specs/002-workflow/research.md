---
id: SPEC-FEAT-002-RESEARCH
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Research: Workflow

## Decision: VN stocks and US stocks are current workflow scope

VN and US stocks prove the current equity research workflow surface while keeping
gold, BTC, and other assets out of active scope.

Rationale: The product goal is agentic financial trading research advice, but data
access and safety scope must stay bounded. Two equity markets are enough for the
current workflow contract.

Alternatives considered: VN stocks plus gold, all markets, or crypto. Rejected
because the current scope is VN stocks and US stocks only.

## Decision: Use fixed workflow execution before flexible chatflow

Fixed workflows provide predictable, testable analysis paths and make evidence,
citations, freshness, chart artifacts, and run inspection easier to verify.

Alternatives considered: production flexible agentic Q&A first. Rejected because
trusted-source retrieval and chatflow safety need a separate bounded spec.

## Decision: Make workflows composable

Phase 02 workflows should be reusable steps that can be run alone or as part of a
larger composite workflow. `stock-brief` is the first composite workflow and runs
`data-collector`, `data-quality-check`, `fundamental-analysis`,
`technical-analysis`, `news-digest`, and `risk-review` as ordered stages.

Rationale: Composition avoids duplicating collection, quality checks, citations,
freshness handling, and stage status across each user-facing workflow.

Alternatives considered: independent monolithic workflow implementations.
Rejected because they make evidence, quality gating, partial failure, and future
workflow reuse harder to keep consistent.

## Decision: Use hybrid YAML workflow definitions and Markdown agent skills

Workflow structure should be machine-readable YAML, while per-analysis behavior
should live in governed Markdown agent skills. Fixed runtime code enforces
validation, data-quality gates, citations, freshness, safety, and output
contracts.

Rationale: YAML definitions keep workflows portable for UI/API tests and future
Claude or MCP-style integrations. Markdown skills keep analysis behavior readable
and easier to evolve without letting instructions replace runtime guardrails.

Alternatives considered: fixed code only, Markdown skills only, and YAML
definitions only. Rejected because each misses either portability, deterministic
validation, or analyst guidance.

## Decision: Keep data collection and quality checks internal

`data-collector` and `data-quality-check` are internal workflow steps, not primary
user-facing workflows in Phase 02. Users see source coverage, freshness,
warnings, blocking issues, and unavailable sections when relevant.

Rationale: Users need trustworthy results, not operational noise. Internal gates
can protect claims while keeping the UI focused on research output.

Alternatives considered: exposing data-quality-check as a standalone workflow.
Deferred until there is enough operational need for a diagnostics-focused view.

## Decision: Use seeded/demo repositories for workflow validation

Seeded/demo canonical records allow contract-first validation before native
realtime market data and news integration are available.

Alternatives considered: live data integration in this feature. Rejected because
source rights, provider reliability, and production freshness rules need later
planning.

## Source Review: TradingAgents

Source: https://github.com/tauricresearch/tradingagents

Useful ideas for Phase 02:

- Split workflow outputs into analyst-style sections: fundamentals, sentiment or
  news, technical analysis, and risk management.
- Preserve a debate-like balance through bull/bear or upside/downside framing
  without implementing autonomous trading decisions.
- Keep a visible run/progress model so users can see which analysis stages are
  complete, partial, failed, or unavailable.

Rejected for Phase 02:

- Trader, portfolio manager, simulated exchange, order execution, and autonomous
  decision steps. FinMind must remain advice support only.

## Source Review: equity-research-vn

Source: https://github.com/Thanhtran-165/equity-research-vn

Useful ideas for Phase 02:

- Treat the workflow suite as a repeatable pipeline: data collection, fundamental
  analysis, valuation, technical analysis, news digest, and report/dashboard
  presentation.
- Include VN-specific data-quality checks such as split-adjusted price handling,
  changed share counts, stale ratio data, source period mismatches, and
  inconsistent EPS/BVPS bases.
- Include bull/bear framing, catalysts, and an independent view instead of a
  one-sided recommendation.
- Allow peer/industry comparison when peer data is available.

Rejected for Phase 02:

- Full HTML dashboard generation/deploy and broad provider-specific ingestion.
  Phase 02 should produce UI-runnable workflow results and artifacts inside
  FinMind, while native realtime data/news ingestion remains a later spec.
