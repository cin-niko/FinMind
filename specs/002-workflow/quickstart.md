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
- Optional live provider credentials/configuration:
  - `FINMIND_US_ALPHA_VANTAGE_API_KEY` for US price/news collection.
  - SEC EDGAR requests must use a configured User-Agent/contact setting before
    live US fundamentals collection is enabled.
  - VN collection uses the configured `vnstock` adapter when installed/enabled.
- Dependencies installed.

## Commands

Task execution starts from [`tasks.md`](tasks.md). Phase 02 should be validated
incrementally after each independently testable user story, then with the full
commands below before completion.

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
2. Confirm `data-collector` requests data through `dataflows`, and `dataflows`
   attempts latest VN provider retrieval through the `vnstock` adapter before
   deterministic fallback is used.
3. Confirm stages include:
   - `data-collector`
   - `data-quality-check`
   - `fundamental-analysis`
   - `technical-analysis`
   - `news-digest`
   - `risk-review`
4. Confirm result includes data-quality status, collection status, sections,
   citations, freshness, chart artifact, and visible execution status.

## Scenario 3: US Stock Workflow

1. Run `technical-analysis` or `stock-brief` with `market=US_STOCK` and a
   supported symbol such as `AAPL`.
2. Confirm `data-collector` requests data through `dataflows`, and `dataflows`
   attempts latest US provider retrieval through Alpha Vantage for prices/news
   when configured and SEC EDGAR company facts for fundamentals where available.
3. Confirm output uses US stock records, not VN stock defaults.
4. Confirm citations and freshness reference US datasets and provider/fallback
   source identity.

## Scenario 4: Provider Failure Or Fallback

1. Run a workflow with live provider credentials disabled or with a forced
   provider failure in tests.
2. Confirm `collection.status` is `partial`, `failed`, or `fallback`.
3. Confirm `collection.provider_results` identifies the failed/skipped/fallback
   provider without raw provider payloads or secrets.
4. Confirm `data-quality-check` returns `warn`, `partial`, or `fail`.
5. Confirm blocked claim categories are omitted or marked unavailable.
6. Confirm fallback data is labeled as fallback and not presented as live data.

## Scenario 5: Quality Gate

1. Run a workflow where one required dataset is missing or stale.
2. Confirm `data-quality-check` returns `warn`, `partial`, or `fail`.
3. Confirm blocked claim categories are omitted or marked unavailable.
4. Confirm unaffected sections remain inspectable for partial results.

## Scenario 6: Unsupported Asset

1. Attempt to run gold, BTC, crypto, or another unsupported asset.
2. Confirm execution is blocked or clearly marked unavailable.
3. Confirm no successful fabricated run is created.

## Scenario 7: Run Reinspection

1. Complete a workflow run.
2. Refresh with a valid session.
3. Open `History` -> `Workflow Runs`.
4. Reopen the completed run and confirm output, quality, collection status,
   citations, freshness, artifacts, and visible execution status remain visible.
