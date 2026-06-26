# FinMind Architecture

System narrative and quality goals for the FinMind platform. **Normative contracts**
remain in [`specs/`](specs/); this document orients readers and agents.

## Purpose

FinMind is an internal finance research workbench: authenticated analysts run fixed
workflows and (planned) evidence-backed chat over canonical market data, with cited
outputs and inspectable lineage — not raw agent reasoning.

V1 user-facing scope: **VN stocks**, **VN100 universe**, daily-canonical price data
with best-effort 1h bars. Roadmap markets (US, gold, BTC) stay behind disabled
surfaces until their owning specs re-enable them.

## Quality goals

1. **Single source of truth** — one canonical row per logical observation; idempotent ingestion.
2. **Evidence-first UX** — material claims cite typed records or are marked unsupported.
3. **Specs before code** — behavior changes start in `specs/system/` or `specs/NNN-slug/`.
4. **Bounded phases** — append-only feature folders; no monolithic V1 spec collapse.
5. **Provider abstraction** — product contracts stay provider-neutral; adapters live in code.

## Architecture decisions

The current architecture is anchored by these accepted ADRs:

| ADR | Decision |
|-----|----------|
| [`ADR-0001`](docs/adr/0001-vn-only-v1-market-scope.md) | V1 market scope is VN100 only; US, gold, and BTC are roadmap. |
| [`ADR-0002`](docs/adr/0002-daily-canonical-vn-price-data.md) | `vn_prices_daily` is canonical; 1h bars are best-effort. |
| [`ADR-0003`](docs/adr/0003-vn100-universe-and-lazy-fetch.md) | VN100 is statically seeded; in-universe tickers may lazy-fetch daily data. |
| [`ADR-0004`](docs/adr/0004-dormant-roadmap-market-connectors.md) | Roadmap market connectors stay dormant in code instead of being deleted. |
| [`ADR-0005`](docs/adr/0005-phase-003-m1-m2-chat-milestones.md) | Phase 003 ships chat-over-prices before fundamentals-cited chat. |
| [`ADR-0006`](docs/adr/0006-shared-evidence-lineage-tables.md) | Shared evidence/citation/artifact/log tables back workflow and chat outputs. |
| [`ADR-0007`](docs/adr/0007-single-timescaledb-store-for-v1.md) | V1 uses one TimescaleDB/PostgreSQL store; ClickHouse and S3/MinIO are deferred. |

## Logical architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  UI (React/Vite) — Workflow, Market, Admin, Chat (planned)  │
└────────────────────────────┬────────────────────────────────┘
                             │ session-authenticated API
┌────────────────────────────▼────────────────────────────────┐
│  Product API (FastAPI) — routes, auth, orchestration        │
│  ├─ workflows / runs                                        │
│  ├─ market + admin ingestion endpoints                      │
│  └─ worker scheduled ingestion endpoint                     │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
┌────────────▼──────────────┐   ┌────────────▼────────────────┐
│  Platform services        │   │  Independent workers        │
│  ingestion, freshness,    │   │  historical backfill CLI    │
│  evidence, artifacts      │   │  (historical mode only)     │
└────────────┬──────────────┘   └────────────┬────────────────┘
             │                               │
┌────────────▼───────────────────────────────▼────────────────┐
│  PostgreSQL / TimescaleDB                                 │
│  ├─ hypertables: price OHLCV series                         │
│  ├─ metadata: instruments, collections, ingestion_jobs    │
│  └─ lineage: evidence_objects, citations, artifacts, logs │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  Source connectors (mock | vnstock, roadmap adapters)       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Agent substrate (src/agent_core) — reusable tools, settings  │
└─────────────────────────────────────────────────────────────┘
```

## Repository map

| Layer | Path | Role |
|-------|------|------|
| Specs | [`specs/`](specs/) | Normative behavior and contracts |
| Backend | [`src/api/`](src/api/) | Product API and platform services |
| Agent core | [`src/agent_core/`](src/agent_core/) | Shared agent/tool substrate |
| Frontend | [`src/ui/`](src/ui/) | Analyst workbench UI |
| Migrations | [`src/api/platform/storage/sql/`](src/api/platform/storage/sql/) | Timescale schema |
| Tests | [`tests/`](tests/) | Verification |

## Feature phases (current order)

See [`AGENTS.md`](AGENTS.md) §9 and [`specs/README.md`](specs/README.md).

## Related documents

- Governance: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- State and API contracts: [`specs/system/state-model.md`](specs/system/state-model.md), [`specs/system/contracts.md`](specs/system/contracts.md)
- Runtime and security: [`specs/system/runtime-config-security.md`](specs/system/runtime-config-security.md)
- Deployment: [`DEPLOYMENT.md`](DEPLOYMENT.md)
- Decisions: [`docs/adr/`](docs/adr/)
- Risks: [`docs/risks/`](docs/risks/)
