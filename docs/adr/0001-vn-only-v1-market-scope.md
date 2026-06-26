---
id: ADR-0001
title: Scope V1 to VN stocks only (VN100 universe)
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/002-data-operations/spec.md
  - specs/system/runtime-config-security.md
  - specs/README.md
---

# ADR-0001: Scope V1 to VN stocks only (VN100 universe)

## Context

Phase 002 initially targeted VN stocks, US markets, XAUUSD, and SJC gold across
multiple free providers (vnstock, yfinance, Alpha Vantage, SJC official). Free
sources proved fragile for multi-market historical and intraday coverage: US/Gold
7-day backfills were unstable, VN long-range 1h history was paused, and operator
complexity grew (many presets, overlap rules, and freshness paths).

The product vision (Perplexity Finance–style AI research) remains valid, but
operating three markets on free data blocked a credible V1 ship. Vietnam is the
home market, vnstock daily history is more tractable than US+gold combined, and
a bounded VN100 universe reduces rate-limit and seeding cost.

## Decision

**V1 user-facing market scope is VN stocks only**, limited to a pre-seeded **VN100**
instrument universe. US stocks, XAUUSD, SJC gold, and BTC are **roadmap markets**:
they must return clear out-of-scope behavior in V1 surfaces and must not appear as
enabled workflow, market, or chat choices.

Normative scope is recorded in Session 2026-06-25 clarifications in
`specs/002-data-operations/spec.md` and `specs/system/runtime-config-security.md`.

## Consequences

### Positive

- One provider family (`vnstock` + `mock`) for V1 ingestion and freshness.
- Clear product story: depth on one market vs. shallow multi-market coverage.
- Aligns with free-resource reality and reduces operator backfill presets.

### Negative / trade-offs

- No US/gold chat or market views in V1; comparisons to Perplexity Finance are
  limited until roadmap markets re-enable.
- Existing US/XAUUSD/SJC implementation work stays in repo but off the V1 path.

### Neutral

- FR numbering preserved; superseded FRs marked rather than deleted (append-only
  spec history).

## Alternatives considered

### Option A: Continue multi-market V1 (VN + US + Gold)

- Pros: Broader demo surface; closer to global finance products.
- Cons: Free providers cannot sustain reliable history; ongoing operator firefighting.
- **Rejected** on 2026-06-25.

### Option B: Gold-only or US-only instead of VN-only

- Pros: Better free daily depth for US; gold as macro overlay.
- Cons: VN is the intended primary user market; US/gold do not replace local equity
  workflow value.
- **Rejected**; VN-only chosen.

### Option C: Open universe (any valid VN ticker on demand)

- Pros: Flexible for ad-hoc tickers.
- Cons: Unbounded ingestion and weaker scope gates for chat/workflows.
- **Rejected**; VN100 boundary with out-of-scope for outsiders (see ADR-0002).

## References

- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — Session 2026-06-25
- [`specs/system/runtime-config-security.md`](../../specs/system/runtime-config-security.md) — Scope Gates
- [`docs/research/perplexity-finance.md`](../../docs/research/perplexity-finance.md) — benchmark context
- [`docs/risks/README.md`](../../docs/risks/README.md) — R-002
