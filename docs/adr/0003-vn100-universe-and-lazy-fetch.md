---
id: ADR-0003
title: VN100 static seed and lazy daily fetch on first access
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/002-data-operations/spec.md
  - specs/002-data-operations/tasks.md
---

# ADR-0003: VN100 static seed and lazy daily fetch on first access

## Context

VN-only V1 (ADR-0001) needs a **bounded instrument universe** so ingestion, market
UI, chat scope gates, and free-provider rate limits stay predictable. Pre-fetching
daily history for all VN100 tickers before any user activity is expensive and slow
on free APIs.

Users expect tickers to work when selected even if no price rows exist yet—without
open-ended on-demand creation of arbitrary HOSE/HNX symbols outside the product
boundary.

## Decision

1. **Pre-seed metadata only** for the VN100 universe: `market_instruments` +
   `VN100` collection memberships from a **static CSV** at `data/seed/vn100.csv`,
   refreshed on a quarterly cadence (not a live vnstock pull at seed time).

2. **Lazy daily fetch:** when a chart or workflow requests a **VN100** instrument
   with no `vn_prices_daily` rows, the ingestion service triggers one inline
   `latest` + `period` daily fetch through the canonical idempotent path, subject
   to overlap blocking and rate guards. **No `historical` mode** on this path.

3. **Out-of-universe tickers** (not in VN100) return clear out-of-scope status;
   no instrument creation and no ingestion attempt.

Historical multi-day backfill remains the **independent worker** only (ADR-0004
companion: web API rejects inline `historical`).

## Consequences

### Positive

- Fast V1 boot: metadata without waiting for 100× daily backfill.
- Scope honesty for chat/workflows (VN100 boundary).
- Same idempotent upsert path as scheduled and manual ingestion.

### Negative / trade-offs

- CSV must be maintained when VN100 constituents change (quarterly refresh discipline).
- First view of a ticker may show loading + lazy-fetch latency.
- Operators still run `vn-history` worker for bulk historical depth.

### Neutral

- VN30/sector collections remain supported entities populated from the VN100 seed.

## Alternatives considered

### Option A: Dynamic vnstock pull at seed time

- Pros: Always current constituents.
- Cons: Requires network at seed; less deterministic for tests and CI.
- **Rejected**; static CSV default with optional refresh workflow.

### Option B: Pre-seed metadata only; no lazy fetch (reject until admin ingests)

- Pros: No inline provider calls on read path.
- Cons: Poor UX; empty charts until operator runs bulk jobs.
- **Rejected**.

### Option C: Open universe (lazy fetch any valid VN symbol)

- Pros: Maximum flexibility.
- Cons: Unbounded ingestion; weak alignment with V1 scope gates.
- **Rejected** (see ADR-0001).

## References

- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — FR-008h, FR-010q
- Tasks T043 (seed), T044 (lazy fetch)
- ADR-0001, ADR-0002
