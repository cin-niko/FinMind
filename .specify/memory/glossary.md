# FinMind Glossary

Canonical vocabulary for specs, code, and agent context. Normative behavior
lives in [`specs/`](../../specs/); this file defines terms only.

## Product and scope

| Term | Definition |
|------|------------|
| **FinMind** | Internal finance research workbench (workflow-first, evidence-backed). |
| **V1** | Current user-facing product scope unless a spec explicitly widens it. |
| **VN100** | Pre-seeded VN stock universe (constituent list + collection). V1 instrument boundary. |
| **Roadmap market** | US stocks, XAUUSD, SJC gold, BTC — connector code may exist but V1 surfaces stay disabled. |

## Spec Kit and phases

| Term | Definition |
|------|------------|
| **Phase / feature folder** | Bounded capability under `specs/NNN-slug/` (e.g. `002-data-operations`). |
| **System spec** | Shared contract under `specs/system/` (state, API rules, runtime, UI). |
| **FR / SC** | Functional requirement / success criterion ID in feature specs. |
| **SDD** | Spec-driven development — specs before code. |

## Data and ingestion

| Term | Definition |
|------|------------|
| **Canonical store** | PostgreSQL-compatible TimescaleDB selected by `FINMIND_DATABASE_URL`. |
| **Dataset** | Logical ingestion product id (e.g. `vn_prices_daily`, `vn_prices`). |
| **Source connector** | Adapter behind `FINMIND_*_PROVIDER`; normalizes provider output to typed schemas. |
| **Hypertable** | TimescaleDB time-partitioned table for OHLCV and quote series. |
| **Lazy fetch** | On-first-access `latest`+`period` ingestion for a VN100 ticker with no daily rows. |
| **Independent backfill** | CLI worker for `historical` range fetches; never inline in the web API. |

## Evidence and outputs

| Term | Definition |
|------|------------|
| **Evidence object** | Grounding unit linking a claim to source records + freshness. |
| **Citation** | User-visible footnote pointing to an evidence object. |
| **Artifact** | Renderable output (chart, table, computed result) with evidence refs. |
| **Execution log** | User-visible event timeline for a run or ingestion job (not raw reasoning). |
| **Freshness** | `fresh`, `stale`, `missing`, or `failed` per dataset rules. |

## Milestones (Phase 003)

| Term | Definition |
|------|------------|
| **003.M1** | Chat over Phase 002 price data with citations and charts. |
| **003.M2** | Fundamentals layer + chat citing financial facts and earnings. |

## External references

| Term | Definition |
|------|------------|
| **vnstock** | VN market data provider adapter for `FINMIND_VN_PROVIDER=vnstock`. |
