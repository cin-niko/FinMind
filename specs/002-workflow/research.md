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

## Decision: Fetch latest provider data with deterministic fallback

Phase 02 should fetch latest available provider data for requested VN and US
stock symbols before workflow analysis runs. Deterministic seeded records remain
only for tests, local offline development, and explicit degraded fallback paths.

Rationale: User-facing workflows need current evidence to be useful as trading
research support. Keeping provider output normalized behind canonical records
preserves testability, citation/freshness enforcement, and future provider
replacement.

Alternatives considered: demo-only repositories. Rejected because demo-only data
cannot satisfy the phase 02 workflow goal once users run live stock research.

## Decision: Build `dataflows` as the shared retrieval layer

Provider retrieval should live in `src/api/platform/dataflows/`, not inside
workflow execution. The module is retrieval-first for workflows and future
chatflow; it does not implement admin ingestion, scheduled backfill, warehouse
storage, or a broad realtime data platform in Phase 02.

Rationale: Workflows and chatflow both need current, evidence-ready finance data,
but neither should know provider APIs or fallback rules. A dedicated retrieval
boundary keeps provider selection, normalization, failure handling, and fallback
labeling in one place while preserving the existing workflow runtime as the
analysis/orchestration layer.

Alternatives considered: keep provider calls in `workflows/collector.py`, build a
full ingestion/backfill platform, or copy TradingAgents-style dataflows directly.
Provider calls inside workflows would couple analysis to source mechanics. A full
ingestion platform is beyond short-term scope. TradingAgents is useful as a
reference, but FinMind needs stricter canonical contracts, provider status,
fallback labeling, and no trading/autonomous action coupling.

## Decision: Use `vnstock` for VN market collection

The VN provider adapter should use `vnstock` for VN stock price and fundamental
collection where the requested symbol and dataset are supported. Critical VN
fundamental claims should keep source identity and period metadata so later
cross-checking against CafeF, exchange disclosures, or company/audited reports is
possible.

Rationale: The referenced `equity-research-vn` collector flow uses `vnstock` as
the primary VN collection path and treats source freshness/period quality as a
first-class workflow concern. This matches FinMind's VN stock scope and
data-quality gate design.

Alternatives considered: scraping individual VN websites first, manual CSVs, or
demo-only VN data. Rejected because they are less reusable, harder to normalize,
or not current enough for workflow output.

## Decision: Use Alpha Vantage plus SEC EDGAR for US market collection

The US provider layer should use Alpha Vantage for latest/daily prices and market
news/sentiment when an API key is configured, and SEC EDGAR company facts for
public-company fundamentals where available. Provider output must be normalized
into canonical price, fundamental, and source-document records.

Rationale: Alpha Vantage provides documented stock time-series and news endpoints
with API-key authentication suitable for an adapter boundary. SEC EDGAR company
facts are public company fundamentals from the primary disclosure source. This
combination avoids relying on unofficial Yahoo Finance access for production
contracts while still allowing a future yfinance adapter if licensing and usage
constraints are explicitly accepted.

Alternatives considered: yfinance, Stooq, Polygon, Finnhub, IEX Cloud, Nasdaq
Data Link, and demo-only US data. yfinance is useful for prototyping but its
project documentation points users to Yahoo terms and personal-use constraints,
so it should not be the default production contract. Paid/commercial APIs can be
added later behind the same provider interface.

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
  FinMind, while broad ingestion, persistence, and dashboard publishing remain
  later specs.
