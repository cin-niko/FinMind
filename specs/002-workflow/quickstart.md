---
id: SPEC-FEAT-002-QUICKSTART
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Quickstart: Workflow Validation

## Prerequisites

- Admin credentials configured:
  - `FINMIND_ADMIN_USERNAME`
  - `FINMIND_ADMIN_PASSWORD`
  - `FINMIND_SESSION_SECRET`
- Dependencies installed.

## Commands

Backend/API verification:

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py
```

Frontend verification:

```bash
cd src/ui
npm run build
```

## Scenario 1: Catalog

1. Log in through the MVP UI shell.
2. Open `Workflows`.
3. Confirm catalog includes:
   - `fundamental-analysis`
   - `technical-analysis`
   - `news-digest`
   - `risk-review`
   - `stock-brief`
4. Confirm each catalog card shows purpose, markets, required inputs, stages, and
   chart/citation expectations.

## Scenario 2: VN Stock Brief

1. Run `stock-brief` with `market=VN_STOCK` and a supported symbol such as `VCB`.
2. Confirm stages include:
   - `data-collector`
   - `data-quality-check`
   - `fundamental-analysis`
   - `technical-analysis`
   - `news-digest`
   - `risk-review`
3. Confirm result includes data-quality status, sections, citations, freshness,
   chart artifact, and visible execution status.

## Scenario 3: US Stock Workflow

1. Run `technical-analysis` or `stock-brief` with `market=US_STOCK` and a
   supported symbol such as `AAPL`.
2. Confirm output uses US stock records, not VN stock defaults.
3. Confirm citations and freshness reference US datasets.

## Scenario 4: Quality Gate

1. Run a workflow where one required dataset is missing or stale.
2. Confirm `data-quality-check` returns `warn`, `partial`, or `fail`.
3. Confirm blocked claim categories are omitted or marked unavailable.
4. Confirm unaffected sections remain inspectable for partial results.

## Scenario 5: Unsupported Asset

1. Attempt to run gold, BTC, crypto, or another unsupported asset.
2. Confirm execution is blocked or clearly marked unavailable.
3. Confirm no successful fabricated run is created.

## Scenario 6: Run Reinspection

1. Complete a workflow run.
2. Refresh with a valid session.
3. Open `History` -> `Workflow Runs`.
4. Reopen the completed run and confirm output, quality, citations, freshness,
   artifacts, and execution status remain visible.
