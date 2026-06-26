---
id: SPEC-FEAT-002-QUICKSTART
feature: data-operations
status: active
owner: solo
created: 2026-06-18
last_review: 2026-06-25
implements:
  - data/seed/vn100.csv
  - scripts/seed_vn100.sh
  - src/api/platform/ingestion/seed.py
  - src/api/platform/ingestion/free_sources.py
  - src/api/platform/ingestion/service.py
  - src/api/platform/ingestion/backfill.py
  - src/api/platform/storage/sql/001_phase002_timeseries.sql
  - src/api/platform/storage/postgres.py
  - src/api/platform/freshness.py
  - src/api/routes/market.py
  - src/api/routes/admin.py
  - src/ui/src/features/market/MarketPage.tsx
  - src/ui/src/features/admin/AdminIngestionPage.tsx
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/ui/src/features/market/MarketPage.test.ts
  - src/ui/src/features/admin/adminIngestionViewModel.test.ts
  - src/ui/src/features/charts/chartViewModel.test.ts
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0002-daily-canonical-vn-price-data.md
  - docs/adr/0003-vn100-universe-and-lazy-fetch.md
  - docs/adr/0004-dormant-roadmap-market-connectors.md
  - docs/adr/0007-single-timescaledb-store-for-v1.md
---

# Quickstart: Data Operations Validation (VN-only V1)

This quickstart walks through the canonical end-to-end flow for the
Phase 002 VN-only V1 scope. Roadmap-market flows (US, XAUUSD, SJC) are
preserved as superseded references at the bottom of this file and only
reachable when the operator explicitly opts in via
`FINMIND_ROADMAP_MARKETS=true`.

## V1 scope at a glance

- Market scope: **VN stocks only**, universe = **VN100** (HOSE-listed).
- Canonical timeframe: **`vn_prices_daily`** (daily OHLCV).
- Best-effort timeframe: **`vn_prices`** (1h, within the vnstock
  rolling window).
- Universe management: pre-seeded from `data/seed/vn100.csv`. Tickers
  outside VN100 return **out-of-scope** without ingestion.
- Ingestion paths: scheduled (worker), manual (admin), lazy
  (chart/workflow first access), independent backfill (operator CLI).

## Prerequisites

- Docker + Docker Compose
- `uv` (Python tooling) installed locally
- Node.js + npm (for the UI build)

## 1. Bring up TimescaleDB

```bash
docker compose up -d timescaledb
```

Confirm health:

```bash
docker compose ps timescaledb
```

## 2. Configure runtime environment

Copy the sample and edit:

```bash
cp .env.sample .env
```

Required for V1:

- `FINMIND_DATABASE_URL` — Postgres DSN pointing at the Compose
  TimescaleDB.
- `FINMIND_VN_PROVIDER=vnstock` for Phase 002 real VN data. Use `mock`
  only for deterministic local tests.
- `FINMIND_VNSTOCK_API_KEY` — optional/reserved; keep server-side if set.
- `FINMIND_ROADMAP_MARKETS=false` (default; V1 hides US/XAUUSD/SJC).

Keep all provider keys server-side. Never expose them to the UI or
write them into specs/docs.

## 3. Apply migrations

The schema migration creates `market_instruments`,
`market_collections`, `market_collection_memberships`, the canonical
`vn_prices_daily` hypertable, and the rest of the Phase 002 tables.

```bash
uv run python -m api.platform.storage.bootstrap
```

(If your local bootstrap entrypoint differs, run the project's
migration command. The migration file is
`src/api/platform/storage/sql/001_phase002_timeseries.sql`.)

## 4. Seed the VN100 universe

This loads 100 HOSE-listed constituents into `market_instruments`,
creates the `VN100` collection row, and writes effective-dated
memberships. The script is idempotent — re-running it must not
duplicate rows and must not shift `effective_from`.

```bash
./scripts/seed_vn100.sh
```

Verify:

```bash
psql "$FINMIND_DATABASE_URL" -c \
  "SELECT count(*) FROM market_instruments WHERE market='VN';"
# expect: 100

psql "$FINMIND_DATABASE_URL" -c \
  "SELECT count(*) FROM market_collection_memberships
     WHERE collection_id='VN100';"
# expect: 100
```

The CSV is refreshed quarterly out-of-band. To refresh, replace
`data/seed/vn100.csv` and re-run `./scripts/seed_vn100.sh`.

## 5. Trigger a scheduled daily fetch (worker path)

Scheduled ingestion is invoked through a protected worker endpoint
(production) or directly via the backfill module (local validation).
For canonical daily data:

```bash
uv run python -m api.platform.ingestion.backfill \
  --source-id vn_prices_daily \
  --from-date 2026-06-18 \
  --to-date 2026-06-25
```

Expected: `vn_prices_daily` rows persisted, one ingestion job logged
with `trigger=backfill`, non-secret diagnostics, and no duplicates on
re-run for the same period.

## 6. Trigger an admin manual rerun

Log in as admin, open the Admin Ingestion page, and trigger a manual
fetch for `vn_prices_daily`. Re-run the same period and confirm:

- The second run does NOT create duplicate time-series rows
  (idempotent upsert by `(market, instrument_id, trade_date)`).
- A concurrent overlapping request returns `status=blocked` with a
  clear message ("vn_prices_daily for … is already running").
- Attempting `mode=historical` through the web API is rejected with
  instructions to use the independent backfill worker.

## 7. Exercise lazy on-first-access daily fetch

Open the Market page in the UI and click any VN100 ticker that does
not yet have `vn_prices_daily` rows. Expected behavior:

- The instrument chart calls
  `IngestionService.ensure_dataset_rows("vn_prices_daily",
  instrument_id)`.
- The chart response includes a `lazy_fetch` field with one of:
  `success`, `already_present`, `blocked`, `failed`, `out_of_scope`.
- On `success` or `already_present`: chart renders with the canonical
  `1d` timeframe and the freshness banner reflects the latest
  `trade_date`.
- On `blocked`: a "Loading latest VN daily data…" banner is shown
  with an auto-refresh after ~5s.
- On `failed`: a non-blocking warning is shown and any existing rows
  render.
- For a ticker NOT in VN100: response contains
  `lazy_fetch.status="out_of_scope"`, no ingestion job is created, no
  instrument row is inserted, and the chart shows a clear
  "Not in VN100 universe (V1 scope)" empty state.

Verify on the database side:

```bash
psql "$FINMIND_DATABASE_URL" -c \
  "SELECT instrument_id, count(*) FROM vn_prices_daily
     GROUP BY instrument_id ORDER BY 1 LIMIT 5;"
```

## 8. Inspect freshness

The admin freshness view and the chart freshness banner are sourced
from `store.freshness()`. With `FINMIND_ROADMAP_MARKETS=false`, the
output contains rows only for `vn_prices_daily` and `vn_prices`.

Threshold rules (V1):

- `vn_prices_daily`: `fresh` when the latest `trade_date` is ≤ 1 VN
  trading day behind today in `Asia/Ho_Chi_Minh`. `stale` otherwise.
- `vn_prices` (1h, best-effort): `fresh` when the latest
  `interval_start` is within 6 hours of now in `Asia/Ho_Chi_Minh`.
  `stale` otherwise.
- `missing`: no records.
- `failed`: latest ingestion job for the dataset is `failed`.

## 9. Run the operator backfill

The default operator preset is now `vn-history`. It runs the canonical
daily leg (required) and a best-effort 1h leg clamped to the rolling
vnstock window.

```bash
docker compose --profile backfill run --build --rm backfill

# local-module equivalent:
./scripts/backfill_market_history.sh
uv run python -m api.platform.ingestion.backfill \
  --preset vn-history \
  --from-date 2026-06-18 \
  --to-date 2026-06-25
```

Expected: the daily leg writes `vn_prices_daily` rows; the 1h leg
either writes or is downgraded to `skipped` with a reason if vnstock
rate-limits or the source is not configured. Idempotent on re-run.

## 10. Run the UI

```bash
cd src/ui
npm install
npm run build
```

Open the app. In V1:

- The header has no market selector.
- The Market page renders the VN overview directly (VN100 + VN30 +
  index strip).
- US/XAUUSD/SJC mini charts, heatmap rows, and instrument rows are
  hidden behind the `roadmapMarketsEnabled` client flag (default
  `false`).
- The instrument detail chart defaults to `1d` with `1h`/`4h`/`1M`
  selectors. `1h` carries a "best-effort coverage" hint.
- The Admin Ingestion page lists only `vn_prices_daily` and
  `vn_prices` datasets.

## Verification

Run the full backend test suite:

```bash
uv run pytest
```

Run the UI test suite:

```bash
cd src/ui
npm test
```

All tests must be green.

---

## Roadmap markets (out of V1 scope)

The following flows are preserved as code paths but are gated behind
`FINMIND_ROADMAP_MARKETS=true`. They are not part of V1 user-facing
behavior. Operators with explicit need MAY re-enable them by setting
the flag and using the original presets:

```bash
FINMIND_ROADMAP_MARKETS=true \
uv run python -m api.platform.ingestion.backfill \
  --preset market-latest

FINMIND_ROADMAP_MARKETS=true \
uv run python -m api.platform.ingestion.backfill \
  --preset market-history \
  --from-date 2026-06-18 \
  --to-date 2026-06-25

FINMIND_ROADMAP_MARKETS=true \
uv run python -m api.platform.ingestion.backfill \
  --preset us-daily-history \
  --from-date 2026-06-18 \
  --to-date 2026-06-25
```

With the flag off (default), these presets short-circuit with
`status=skipped` and `reason="roadmap markets disabled
(FINMIND_ROADMAP_MARKETS=false)"`. See
[ADR-0004](../../docs/adr/0004-dormant-roadmap-market-connectors.md)
for the rationale.

## Related documents

- [Phase 002 spec](./spec.md)
- [Phase 002 plan](./plan.md)
- [Phase 002 tasks](./tasks.md)
- [System runtime + security](../system/runtime-config-security.md)
- [DEPLOYMENT.md](../../DEPLOYMENT.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
