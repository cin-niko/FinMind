# Free Market Data Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the phase 002 free-source provider profile for FireAnt VN stocks,
yfinance/Yahoo Finance XAUUSD, Alpha Vantage daily XAUUSD fallback, and official SJC
daily quotes.

**Architecture:** Keep provider-specific fetching inside ingestion adapters that return
canonical `TimeSeriesRecord` objects. Persist all normalized records through the
existing store abstraction and add a daily XAUUSD fallback table/repository path.

**Tech Stack:** Python 3.12, FastAPI, httpx, psycopg, pytest, PostgreSQL/TimescaleDB.

---

### Task 1: Runtime Provider Profile

**Files:**
- Modify: `src/api/settings.py`
- Modify: `src/api/platform/factory.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing settings tests**

Add tests that set `FINMIND_PROVIDER_PROFILE=free` with
`FINMIND_VN_PROVIDER=fireant`, `FINMIND_XAUUSD_PROVIDER=yfinance`,
`FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`, and
`FINMIND_SJC_PROVIDER=sjc_official`, then assert `create_app()` builds the platform.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py -q`

- [ ] **Step 3: Implement runtime selection**

Add provider profile fields to `Settings` and route `provider_profile == "free"` to a
new `create_free_sources()` factory.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py -q`

### Task 2: Free Source Adapter Module

**Files:**
- Create: `src/api/platform/ingestion/free_sources.py`
- Test: `tests/test_platform_services.py`

- [ ] **Step 1: Write failing adapter factory tests**

Assert `create_free_sources()` returns sources for `vn_prices`, `xauusd_prices`,
`xauusd_prices_daily`, and `sjc_gold_prices`, and that each source id matches its
canonical dataset id.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py -q`

- [ ] **Step 3: Implement minimal adapter classes**

Implement provider classes with `fetch(period: str) -> list[TimeSeriesRecord]`.
Use injected HTTP/session callables in tests so no network is required.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py -q`

### Task 3: FireAnt VN Stock Adapter

**Files:**
- Modify: `src/api/platform/ingestion/free_sources.py`
- Test: `tests/test_platform_services.py`

- [ ] **Step 1: Write failing normalization test**

Use a fake FireAnt response with symbol, exchange, 1h interval times, OHLCV, and traded
value. Assert normalized `vn_prices` records match `stock_1h_bars` payload fields and
include capability diagnostics for the covered range.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py::test_fireant_adapter_normalizes_vn_stock_bars -q`

- [ ] **Step 3: Implement FireAnt parsing**

Normalize FireAnt bars into `TimeSeriesRecord(dataset_id="vn_prices", ...)` and fail
with non-secret diagnostics when required fields are missing.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py::test_fireant_adapter_normalizes_vn_stock_bars -q`

### Task 4: XAUUSD Intraday And Daily Fallback

**Files:**
- Modify: `src/api/platform/ingestion/free_sources.py`
- Modify: `src/api/platform/storage/sql/001_phase002_timeseries.sql`
- Modify: `src/api/platform/storage/postgres.py`
- Test: `tests/test_platform_services.py`

- [ ] **Step 1: Write failing fallback tests**

Assert recent yfinance-style 1h records normalize to `xauusd_prices`; assert unavailable
1h history returns a capability diagnostic and daily Alpha Vantage-style records
normalize to `xauusd_prices_daily`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py -q`

- [ ] **Step 3: Add daily fallback schema and repository mapping**

Add `xauusd_daily_bars` SQL table/hypertable and PostgreSQL upsert/list mapping for
`xauusd_prices_daily`.

- [ ] **Step 4: Implement yfinance and Alpha Vantage normalization**

Normalize yfinance/Yahoo recent intraday bars into `xauusd_prices`; normalize Alpha
Vantage daily gold history into `xauusd_prices_daily`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py -q`

### Task 5: SJC Official Daily Importer

**Files:**
- Modify: `src/api/platform/ingestion/free_sources.py`
- Test: `tests/test_platform_services.py`

- [ ] **Step 1: Write failing SJC parsing test**

Use a small saved HTML/table fixture string with buy/sell prices. Assert the adapter
returns one `sjc_gold_prices` record, attributes SJC, and omits raw page content from
diagnostics.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py::test_sjc_adapter_parses_daily_quote_without_raw_page_dump -q`

- [ ] **Step 3: Implement SJC parsing**

Parse official SJC page/table content into daily `buy_sell` quotes. Store only source
identity, quote fields, collected time, and safe diagnostics.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py::test_sjc_adapter_parses_daily_quote_without_raw_page_dump -q`

### Task 6: Final Verification

**Files:**
- Modify: `specs/002-data-operations/tasks.md`
- Modify: `README.md`

- [ ] **Step 1: Run backend verification**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest`

- [ ] **Step 2: Run lint**

Run: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --with ruff ruff check src tests`

- [ ] **Step 3: Run UI build**

Run from `src/ui`: `npm run build`

- [ ] **Step 4: Run whitespace check**

Run: `git diff --check`

- [ ] **Step 5: Update task status**

Mark T015-T020 done only when the adapter tests and verification commands pass.
