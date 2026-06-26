---
id: ADR-0007
title: Use a single TimescaleDB-backed PostgreSQL store for V1 data operations
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/002-data-operations/spec.md
  - specs/002-data-operations/data-model.md
  - specs/system/contracts.md
  - ARCHITECTURE.md
---

# ADR-0007: Use a single TimescaleDB-backed PostgreSQL store for V1 data operations

## Context

A reference mature finance architecture separates data by workload:

```text
PostgreSQL       → companies, instruments, financial facts, earnings, estimates
ClickHouse/TSDB  → OHLCV and intraday market data
S3/MinIO         → filings, transcripts, generated reports
```

FinMind V1 is materially smaller: VN100 only, `vn_prices_daily` as canonical, and
`vn_prices` 1h as best-effort. The immediate requirement is reliable ingestion,
idempotent upserts, freshness, and evidence lineage on free VN data, not multi-market
tick-scale analytics or large filing/transcript storage.

Splitting the data plane now would add operational complexity before the product has
enough volume or document workflows to justify it.

## Decision

Use one **PostgreSQL-compatible TimescaleDB** service as the canonical Phase 002/V1
database:

- Timescale hypertables for price time series (`vn_prices_daily`, `vn_prices`, and
  dormant roadmap market tables).
- Regular relational tables for metadata (`market_instruments`, collections,
  ingestion jobs).
- Regular relational tables for evidence lineage (`evidence_objects`, `citations`,
  `artifacts`, `execution_logs`).

Do **not** introduce ClickHouse for V1. Do **not** introduce S3/MinIO in Phase 002 or
Phase 003.M1. Revisit object storage in Phase 003.M2 only if fundamentals/document
workflows require large filings, transcripts, reports, or page-level citation.

## Consequences

### Positive

- One database service, one migration path, one backup/restore story for V1.
- Transactions can connect ingestion jobs, typed market rows, evidence, citations,
  artifacts, and execution logs.
- TimescaleDB is sufficient for VN100 daily and rolling 1h data volumes.
- Lower operational burden for a solo/internal workbench.

### Negative / trade-offs

- Not optimized for very large multi-market intraday scans compared with ClickHouse.
- PostgreSQL JSONB artifact payloads are not a long-term home for large PDFs,
  transcripts, or generated reports.
- Future migration may be needed when roadmap markets, document ingestion, or heavy
  analytics arrive.

### Neutral

- The architecture still preserves extension points: ClickHouse can be added later as
  a read-optimized time-series mirror, and S3/MinIO can be added when document/blob
  use cases appear.

## Alternatives considered

### Option A: PostgreSQL + ClickHouse + S3/MinIO from the start

- Pros: Mature finance stack shape; strong analytical performance and blob storage.
- Cons: More services, more deployment work, more schema synchronization, and no
  current V1 scale need.
- **Rejected** for V1; revisit after VN100 price/chat workflows prove value.

### Option B: Plain PostgreSQL without TimescaleDB

- Pros: Simpler dependency; hosted PostgreSQL is easy to find.
- Cons: We already need time-series partitions/hypertables and validation against the
  production database family.
- **Rejected**; TimescaleDB remains the canonical service for price tables.

### Option C: Store documents/artifacts in object storage now

- Pros: Future-proof for filings and generated reports.
- Cons: No Phase 002 or 003.M1 workflow requires large blobs yet; adds infra early.
- **Deferred** until a concrete Phase 003.M2 document/fundamentals use case requires it.

## References

- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — FR-008a, FR-008b, FR-008e
- [`specs/002-data-operations/data-model.md`](../../specs/002-data-operations/data-model.md) — Storage Decision
- [`specs/system/contracts.md`](../../specs/system/contracts.md) — evidence/artifact/provider contracts
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md) — logical architecture
- [`docs/research/perplexity-finance.md`](../research/perplexity-finance.md) — benchmark architecture comparison
