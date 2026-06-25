---
id: SPEC-FEAT-002-RESEARCH
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---

# Research: Data Operations

## Decision: Keep provider details behind connector contracts

The product contract should define supported datasets, freshness, source identity, and logical canonical observations. Provider licensing, credentials, schemas, and retry behavior belong in source connector implementations.

## Decision: Use deterministic demo sources first

Deterministic VN stock and gold sources allow validation of idempotency, freshness, and UI behavior before free-source adapters are wired into the ingestion runtime.

## Decision: Use per-dataset free provider selection before paid integrations

The first real-source set uses no-cost sources selected independently per dataset:
`vnstock` for VN stock history, yfinance/Yahoo Finance for recent XAUUSD intraday
bars, Alpha Vantage free gold history as XAUUSD daily fallback, and official SJC
website/chart surfaces for SJC daily quotes. `mock` remains the default value for
each dataset so local tests and demos do not require live provider access.

Rationale: The project can validate ingestion, charting, freshness, and PostgreSQL
idempotency without committing to paid licensing. The tradeoff is explicit: free
sources may have rate limits, unofficial API stability risk, recent-only intraday
history, and scraper fragility. The system must expose these as capability diagnostics
and must not synthesize unavailable history.

## Decision: Block unsafe overlap

Multiple jobs for the same dataset and period can corrupt freshness interpretation or duplicate records. The service blocks later overlapping requests with visible status while the earlier job is queued or running.

## Decision: Expose an external scheduler/worker API contract

Scheduled ingestion is invoked through a protected worker-facing API endpoint rather than relying only on in-process app startup or demo history. This keeps the scheduling boundary explicit and testable against canonical PostgreSQL storage.

## Decision: Limit initial populated datasets

The initial implementation populates chart-ready `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`. Source contracts preserve extension points for indicators, company reports, macro/news, and other approved workflow source material without requiring those datasets to be populated in the initial build.

`xauusd_prices_daily` is added as a fallback dataset for long-history XAUUSD charts
when free 1h intraday coverage is unavailable.
