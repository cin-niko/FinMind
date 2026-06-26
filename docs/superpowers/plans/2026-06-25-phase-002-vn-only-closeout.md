# Phase 002 VN-Only Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 002 against the VN-only V1 scope decided on
2026-06-25 (see `docs/adr/0001-vn-only-v1-market-scope.md`,
`docs/adr/0002-daily-canonical-vn-price-data.md`,
`docs/adr/0003-vn100-universe-and-lazy-fetch.md`,
`docs/adr/0004-dormant-roadmap-market-connectors.md`,
`docs/adr/0006-shared-evidence-lineage-tables.md`,
`docs/adr/0007-single-timescaledb-store-for-v1.md`).

**Architecture:**

- Canonical V1 timeframe is `vn_prices_daily`; `vn_prices` 1h is best-effort.
- One ingestion path serves scheduled, admin manual, lazy on-first-access,
  and independent backfill triggers.
- VN100 universe is pre-seeded from a static CSV; out-of-universe tickers
  return out-of-scope without ingestion.
- US/XAUUSD/SJC code stays dormant behind `FINMIND_ROADMAP_MARKETS` (off
  by default).

**Tech stack:** Python 3.12, FastAPI, Pydantic, vnstock adapter,
PostgreSQL/TimescaleDB via Docker Compose, React/Vite UI with Lightweight
Charts, pytest, Ruff.

**Out of scope (this plan):**

- Phase 003 chat or fundamentals work.
- Re-enabling US/XAUUSD/SJC surfaces.
- Object storage / MinIO infrastructure.

---

## Step 1 — Data Layer Foundation

Goal: typed daily storage, VN daily adapter, and VN100 universe seeded
into `market_instruments`/`market_collections`. Ingestion still flows
through the existing canonical path.

### Task 1 (T041): Add `vn_prices_daily` typed table

**Files:**

- Modify: `src/api/platform/storage/sql/001_phase002_timeseries.sql`
  (or add new migration file under the same folder if append-only is
  preferred for production safety)
- Modify: `src/api/platform/storage/postgres.py` (SELECT/INSERT for new
  table)
- Modify: `src/api/platform/models.py` (if a daily record dataclass is
  required for typed ingestion)
- Test: `tests/test_platform_services.py`

- [ ] Create `vn_prices_daily` typed table keyed by `(market,
      instrument_id, trade_date)` with OHLCV, currency, collected_at,
      source_id, freshness_status, and OHLC integrity checks.
- [ ] Register the table as a TimescaleDB hypertable on `trade_date`.
- [ ] Add unique index `(market, instrument_id, trade_date)` for
      idempotent upserts.
- [ ] Add repository read query mirroring `stock_daily_bars` semantics
      but scoped to VN.
- [ ] Verify with `uv run pytest tests/test_platform_services.py`.

### Task 2 (T042): vnstock daily adapter path

**Files:**

- Modify: `src/api/platform/ingestion/free_sources.py`
- Modify: `src/api/platform/ingestion/sources.py` (if a new source id
  is required)
- Modify: `src/api/platform/ingestion/planner.py` (latest/period
  resolution for daily)
- Test: `tests/test_platform_services.py`

- [ ] Add a daily fetch method on the vnstock adapter that normalizes
      records into the `vn_prices_daily` schema.
- [ ] Reuse the existing planner for `latest` and `period` modes; do
      not introduce new fetch modes.
- [ ] Ensure provider diagnostics use non-secret fields only.
- [ ] Add unit tests with deterministic mock provider responses.

### Task 3 (T043): VN100 universe seed

**Files:**

- Add: `data/seed/vn100.csv` (static, refreshed quarterly)
- Add: `scripts/seed_vn100.sh`
- Add: `src/api/platform/ingestion/seed.py` (or similar) to load CSV
- Modify: `docker-compose.yaml` (optional runner service)
- Test: `tests/test_platform_services.py`

- [ ] Author `vn100.csv` with columns: `symbol`, `display_name`,
      `exchange`, `sector`, `industry`, `currency`, `status`.
- [ ] Seed `market_instruments` with one row per symbol using
      `instrument_id = vn_stock:<SYMBOL>`.
- [ ] Create `VN100` row in `market_collections` and
      effective-dated memberships for each symbol.
- [ ] Make seeding idempotent (re-running the script does not duplicate
      rows).
- [ ] Add a test asserting seed determinism and VN30/VN100 membership
      counts.

**Step 1 checkpoint:** Compose comes up clean. Seed loads 100
instruments. Daily adapter ingests one VN100 ticker through the
existing `latest`/`period` path. Repository can read the new daily
table.

---

## Step 2 — Service Behavior

Goal: hide roadmap surfaces behind a flag, implement lazy fetch with
overlap safety, and narrow freshness output to V1 datasets.

### Task 4 (T047): `vn-history` plan + roadmap flag

**Files:**

- Modify: `src/api/platform/ingestion/backfill.py`
- Modify: `scripts/backfill_market_history.sh`
- Modify: `src/api/settings.py`
- Modify: `.env.sample`
- Modify: `docs/research/perplexity-finance.md` (no change expected;
  verify roadmap references are accurate)
- Test: `tests/test_platform_services.py`

- [ ] Add settings field `FINMIND_ROADMAP_MARKETS` (default `false`).
- [ ] Add `vn-history` preset targeting `vn_prices_daily` (required)
      and `vn_prices` 1h best-effort.
- [ ] Wrap US/XAUUSD/SJC presets so they only run when the flag is
      `true`.
- [ ] Default operator backfill in `scripts/backfill_market_history.sh`
      should be `vn-history`.
- [ ] Add tests that with the flag off, no roadmap dataset is fetched.

### Task 5 (T044): Lazy daily fetch policy

**Files:**

- Modify: `src/api/platform/ingestion/service.py`
- Modify: `src/api/routes/market.py` (chart endpoint integration)
- Modify: `src/api/platform/repositories.py` (helper to detect missing
  rows)
- Test: `tests/test_platform_services.py`

- [ ] When a chart/workflow requests a VN100 instrument with no
      `vn_prices_daily` rows, trigger one inline `latest`+`period`
      daily fetch through the existing ingestion path.
- [ ] Honor the existing overlap guard on
      `(source_id=vn_prices_daily, period)`.
- [ ] Reject out-of-universe tickers with a clear out-of-scope status.
- [ ] Never trigger `historical` mode from this path.
- [ ] Add tests for: in-universe missing rows triggers fetch;
      out-of-universe returns out-of-scope; overlap returns blocked
      status; lazy and scheduled writes converge to the same idempotent
      rows.

### Task 6 (T045): VN-only freshness output

**Files:**

- Modify: `src/api/platform/freshness.py`
- Modify: `src/api/routes/admin.py` (freshness rows in admin response)
- Test: `tests/test_platform_services.py`

- [ ] Compute `fresh|stale|missing|failed` only for `vn_prices_daily`
      (latest VN trading day) and `vn_prices` 1h (latest expected bar
      inside the vnstock rolling window).
- [ ] When `FINMIND_ROADMAP_MARKETS=false`, omit US/XAUUSD/SJC rows
      from the freshness payload.
- [ ] Add tests for each freshness state per dataset.

**Step 2 checkpoint:** Scheduled, admin manual, and lazy fetches all
write through one path. Freshness output is VN-only in V1. Roadmap
markets are reachable only behind the flag.

---

## Step 3 — UI Scope-Down

Goal: align the UI with VN-only V1 surfaces, daily-canonical chart
default, and lazy-fetch UX.

### Task 7 (T046): UI scope-down

**Files:**

- Modify: `src/ui/src/features/market/MarketPage.tsx`
- Modify: `src/ui/src/features/market/marketViewModel.ts` (if
  selectors filter market list)
- Modify: `src/ui/src/features/market/InstrumentDetailChart.tsx` (or
  equivalent) to default to `1d`
- Modify: `src/ui/src/api/client.ts` (lazy-fetch loading + freshness
  banner types)
- Modify: `src/ui/src/features/admin/AdminIngestionPage.tsx` (hide
  roadmap dataset rows when scope is VN-only)
- Modify: `src/ui/src/features/workflows/*` if market choices are
  rendered there

- [ ] Remove the header market selector in V1; render the VN overview
      directly.
- [ ] Default instrument detail chart timeframe to `1d`; allow
      `1h`/`4h`/`1M` selectors with coverage banners for 1h.
- [ ] Show a loading/freshness banner during lazy fetch and a clear
      out-of-scope message for unsupported tickers.
- [ ] Hide US/XAUUSD/SJC mini charts, instrument table rows, and
      heatmap rows in V1.
- [ ] Build the UI with `npm run build` in `src/ui`.

---

## Step 4 — Verification

Goal: Phase 002 closed end-to-end against Docker Compose.

### Task 8 (T048): Test coverage

**Files:**

- Modify: `tests/test_platform_services.py`
- Modify: `tests/test_app.py`

- [ ] VN100 seed determinism and collection counts.
- [ ] Lazy-fetch trigger + overlap guard.
- [ ] Out-of-universe rejection.
- [ ] Daily canonical freshness rules.
- [ ] Default `1d` chart timeframe behavior (UI smoke if feasible,
      otherwise API response).
- [ ] UI scope-down regression (snapshot or component test).

### Task 9 (T049): Rewrite quickstart for VN-only

**Files:**

- Modify: `specs/002-data-operations/quickstart.md`
- Modify: `specs/002-data-operations/plan.md` (sync if commands change)

- [ ] Cover: bring up Compose -> apply migrations -> run VN100 seed
      script -> trigger scheduled `vn_prices_daily` latest -> trigger
      admin manual rerun -> open Market and trigger one lazy fetch ->
      inspect freshness.
- [ ] Mark the old multi-market quickstart sections as superseded and
      preserve them only as roadmap references.
- [ ] Validate quickstart end-to-end against Docker Compose.

### Task 10: Verification commands

**Files:**

- No code files.

- [ ] `uv run pytest`
- [ ] `cd src/ui && npm install && npm run build`
- [ ] Bring up `docker compose up -d timescaledb`, apply migrations,
      run `scripts/seed_vn100.sh`, run a scheduled fetch via worker
      endpoint, run an admin manual rerun, trigger a lazy fetch via the
      UI/chart endpoint.
- [ ] Confirm DB row counts in `vn_prices_daily`, `market_instruments`,
      and `market_collection_memberships`.
- [ ] Confirm no roadmap dataset rows appear with
      `FINMIND_ROADMAP_MARKETS` unset.

---

## Closeout

- [ ] Mark T041–T049 complete in `specs/002-data-operations/tasks.md`.
- [ ] Mark T014 closed as superseded by T049 (already noted in tasks).
- [ ] Update `docs/risks/README.md`: re-evaluate R-001 (provider
      depth) and R-003 (evidence persistence) given current state.
- [ ] Align `specs/002-data-operations/data-model.md` and
      `specs/002-data-operations/contracts/api-contract.md` with the
      VN-only normative scope as a small follow-up spec PR if not done
      earlier.
- [ ] Phase 002 ready for handoff to Phase 003.M1 planning.

## References

- ADR-0001 through ADR-0007 in `docs/adr/`
- `specs/002-data-operations/spec.md`
- `specs/002-data-operations/tasks.md`
- `specs/system/runtime-config-security.md`
- `ARCHITECTURE.md`
- `DEPLOYMENT.md`
