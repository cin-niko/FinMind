# Architecture Decision Records (ADR)

Canonical location for **why** a significant technical or product decision was made.
Normative behavior stays in [`specs/`](../../specs/); ADRs capture context,
decision, consequences, and alternatives.

Decisions get ADRs. Any architectural choice with trade-offs gets a new file in
`docs/adr/` using [`_template.md`](_template.md). Reference it from the affected
spec's `adr_refs:` frontmatter.

## When To Write An ADR

- Choosing a database, ingestion topology, evidence model, or artifact model.
- Changing V1 scope, market boundaries, provider strategy, or security boundaries.
- Splitting or merging feature milestones.
- Accepting a major risk or deferring infrastructure that future agents may re-debate.

## New Decision Workflow

1. Copy the template and pick the next number:

   ```bash
   cp docs/adr/_template.md docs/adr/000N-short-slug.md
   ```

2. Fill out:

   - `Context`
   - `Decision`
   - `Consequences`
   - `Alternatives considered`
   - `References`

3. Update this README's register.
4. Reference the ADR from affected spec frontmatter:

   ```yaml
   adr_refs:
     - docs/adr/000N-short-slug.md
   ```

5. If the decision changes user-facing behavior, also update
   [`ARCHITECTURE.md`](../../ARCHITECTURE.md) and the affected feature/system specs.

`make check-specs` (when enabled) should verify that `adr_refs` paths exist.

## File Naming

```text
docs/adr/000N-short-slug.md
```

- `000N` — zero-padded sequence (`0001`, `0002`, ...)
- `short-slug` — kebab-case topic

The ADR `id` inside frontmatter uses the display form `ADR-000N`.

## Register

| ADR | Title | Status | Decision note | Affected specs |
|-----|-------|--------|---------------|----------------|
| [ADR-0001](0001-vn-only-v1-market-scope.md) | Scope V1 to VN stocks only (VN100 universe) | accepted | Re-confirmed: V1 user-facing market scope is VN100 only; US, gold, and BTC are roadmap. | `002-data-operations`, `runtime-config-security`, `specs/README.md` |
| [ADR-0002](0002-daily-canonical-vn-price-data.md) | Make VN daily bars canonical; 1h best-effort | accepted | Re-confirmed: `vn_prices_daily` is the V1 canonical timeframe; 1h is best-effort. | `002-data-operations` |
| [ADR-0003](0003-vn100-universe-and-lazy-fetch.md) | VN100 static seed and lazy daily fetch on first access | accepted | Re-confirmed: static VN100 seed + bounded lazy fetch; no open instrument creation. | `002-data-operations` |
| [ADR-0004](0004-dormant-roadmap-market-connectors.md) | Keep roadmap market connectors dormant in code | accepted | Re-confirmed: keep US/XAUUSD/SJC code dormant behind roadmap scope instead of deleting. | `002-data-operations`, `runtime-config-security` |
| [ADR-0005](0005-phase-003-m1-m2-chat-milestones.md) | Split Phase 003 into M1 chat-over-prices and M2 fundamentals | accepted | Re-confirmed: close Phase 002 first, ship price-grounded chat, then fundamentals-cited chat. | `003-evidence-backed-chat`, `specs/README.md` |
| [ADR-0006](0006-shared-evidence-lineage-tables.md) | Use shared evidence lineage tables for workflow and chat outputs | accepted | Re-confirmed: evidence/citation/artifact/log tables are the shared proof layer, not chat-only storage. | `state-model`, `contracts`, `002-data-operations`, `003-evidence-backed-chat` |
| [ADR-0007](0007-single-timescaledb-store-for-v1.md) | Use a single TimescaleDB-backed PostgreSQL store for V1 data operations | accepted | Re-confirmed: keep one TimescaleDB/PostgreSQL store for V1; defer ClickHouse and S3/MinIO. | `002-data-operations`, `contracts`, `ARCHITECTURE.md` |
