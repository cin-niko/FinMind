# Latest First 7-Day Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Phase 002 prioritize current/latest market data fetches and reduce the default historical backfill attempt to seven days.

**Architecture:** Keep the web/admin latest fetch path as the canonical current-data path, and add an independent CLI preset for operators to run latest fetches without the web UI. Keep historical backfill independent and reduce its default window to seven days. VN historical remains paused.

**Tech Stack:** Python ingestion service, PostgreSQL/Timescale storage, Docker Compose, pytest, Ruff, Vite UI build.

---

### Task 1: Add Latest-First Operator Preset

**Files:**
- Modify: `src/api/platform/ingestion/backfill.py`
- Test: `tests/test_platform_services.py`

- [ ] Add a `market-latest` preset that runs `latest` mode for `us_prices`, `xauusd_prices`, and `sjc_gold_prices`.
- [ ] Assert the latest preset does not call `vn_prices`.
- [ ] Verify with `pytest tests/test_platform_services.py`.

### Task 2: Reduce Historical Backfill Defaults To Seven Days

**Files:**
- Modify: `docker-compose.yaml`
- Modify: `.env.sample`
- Modify: `scripts/backfill_market_history.sh`
- Modify: `specs/002-data-operations/*`
- Modify: `specs/system/runtime-config-security.md`
- Test: `tests/test_platform_services.py`

- [ ] Change documented/default window to `2026-06-18:2026-06-25`.
- [ ] Change shell script fallback from seven days to seven days.
- [ ] Update tests from one-month expectations to seven-day expectations.

### Task 3: Verify And Run

**Files:**
- No code files.

- [ ] Run backend tests.
- [ ] Run Ruff.
- [ ] Run UI build if frontend files are touched.
- [ ] Rebuild backfill image.
- [ ] Run `market-latest`.
- [ ] Run seven-day `market-history`.
- [ ] Report exact job results and DB counts.
