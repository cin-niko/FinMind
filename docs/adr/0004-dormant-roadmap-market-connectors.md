---
id: ADR-0004
title: Keep roadmap market connectors dormant in code
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/002-data-operations/spec.md
  - specs/002-data-operations/tasks.md
  - specs/system/runtime-config-security.md
---

# ADR-0004: Keep roadmap market connectors dormant in code

## Context

Phase 002 implemented US (`us_prices`, `us_prices_daily`), XAUUSD (yfinance +
Alpha Vantage daily fallback), and SJC gold adapters, plus multi-market backfill
presets (`market-history`, `us-xauusd-history`, `market-latest`). VN-only V1
(ADR-0001) removes these from user-facing ingestion schedules, freshness output,
and market UI—but the code and schemas remain in the repository.

## Decision

**Do not delete** US/XAUUSD/SJC connector code, typed tables, or superseded tasks.
Mark related FRs and tasks as **superseded** in specs. In V1:

- Roadmap env vars remain **recognized** but **must not enable** surfaces.
- Default backfill plan becomes **`vn-history`** (T047); US/Gold presets reachable
  only behind **`FINMIND_ROADMAP_MARKETS`** (off by default).
- Admin/market UI hides roadmap markets (FR-018e).

Re-enablement is a **configuration + spec** change, not a reimplementation.

## Consequences

### Positive

- Reversible scope expansion without git archaeology.
- Tests for roadmap adapters can stay in CI with mocks.
- Aligns with provider abstraction (`specs/system/contracts.md`).

### Negative / trade-offs

- Repo carries dead paths until roadmap re-enable; agents must read V1 scope docs.
- Slightly larger surface for accidental V1 wiring (mitigated by flag + UI scope-down).

### Neutral

- Superseded tasks (T017–T040 subset) preserved with `[SUPERSEDED 2026-06-25]` notes.

## Alternatives considered

### Option A: Remove US/XAUUSD/SJC code now

- Pros: Smaller codebase; no confusion.
- Cons: High rework cost when expanding markets; loses tested adapters.
- **Rejected**.

### Option B: Feature flag only, no spec supersession

- Pros: Minimal doc churn.
- Cons: Normative specs would still claim US/Gold as V1—trust drift.
- **Rejected**; specs updated + code dormant.

### Option C: Keep US/Gold active in V1 with reduced history

- Pros: Multi-market demo.
- Cons: Same free-provider failures that triggered VN-only scope.
- **Rejected** (ADR-0001).

## References

- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — superseded FR-010k–p, FR-018d
- [`specs/system/runtime-config-security.md`](../../specs/system/runtime-config-security.md) — roadmap provider vars
- Task T047 — `FINMIND_ROADMAP_MARKETS`
- ADR-0001
