---
id: ADR-0002
title: Make VN daily bars canonical; 1h best-effort
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/002-data-operations/spec.md
  - specs/002-data-operations/tasks.md
---

# ADR-0002: Make VN daily bars canonical; 1h best-effort

## Context

Free `vnstock` data is asymmetric: **daily** history is relatively deep and usable
for multi-year charts; **1h** history is a shallow, fragile rolling window. Phase
002 originally treated 1h as the primary VN path (same mechanism for backfill and
latest), with production launch gated on partial 1h coverage diagnostics.

Under VN-only V1 (ADR-0001), the product must ship honest long-history charts and
freshness without pretending full intraday depth exists. Perplexity-style products
often emphasize daily resolution for fundamentals and narrative; intraday is a
bonus when available.

## Decision

**`vn_prices_daily` is the canonical V1 timeframe.** Storage, default chart timeframe,
freshness critical path, and lazy-fetch target use the typed daily OHLCV path
(`vn_prices_daily` / `stock_daily_bars`).

**`vn_prices` (1h)** remains ingested over the `vnstock` rolling window as
**best-effort**: coverage gaps are diagnostics, not launch blockers, and missing 1h
must not fail workflows or freshness for the daily canonical path.

Instrument detail charts **default to `1d`**; `4h` and `1M` derive from daily;
`1h` shows explicit coverage banners when bars are missing.

## Consequences

### Positive

- Credible multi-year VN history on free tier after one `vn-history` backfill.
- Freshness rules align with what providers can actually deliver.
- Phase 003.M1 chat can ground on daily series without 1h dependency.

### Negative / trade-offs

- V1 does not promise intraday broker-grade charts for all VN100 names.
- Requires new table/adapter work (tasks T041, T042) before prior 1h-only path is
  complete for V1.

### Neutral

- Existing `stock_1h_bars` schema and vnstock 1h adapter remain; not deleted.

## Alternatives considered

### Option A: 1h canonical (prior Phase 002 direction)

- Pros: Richer intraday UX; single grain for all timeframes.
- Cons: Free vnstock cannot backfill long 1h; blocks credible history story.
- **Superseded** by this ADR on 2026-06-25.

### Option B: Daily-only V1 (drop 1h entirely)

- Pros: Simplest implementation.
- Cons: Loses rolling-window intraday when vnstock does provide it.
- **Rejected**; keep 1h best-effort without blocking V1.

### Option C: Display-only hourly bars synthesized from daily (XAUUSD pattern)

- Pros: Smooth intraday charts without 1h provider data.
- Cons: Misleading for equities if presented as real intraday; rejected for VN
  stocks—honesty over synthetic intraday.
- **Rejected** for VN; daily canonical + real 1h when available.

## References

- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — FR-010r, FR-018c
- ADR-0001 — VN-only scope
- [`docs/risks/README.md`](../../docs/risks/README.md) — R-001
