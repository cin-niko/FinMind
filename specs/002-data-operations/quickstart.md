---
id: SPEC-FEAT-002-QUICKSTART
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Quickstart: Data Operations Validation

## Scenario 1: Admin Ingestion Control

Production-mode setup:

1. Start TimescaleDB/PostgreSQL with Docker Compose.
2. Set `FINMIND_DATABASE_URL` for the API.
3. Keep `FINMIND_VN_PROVIDER=mock`, `FINMIND_XAUUSD_PROVIDER=mock`, and
   `FINMIND_SJC_PROVIDER=mock` for deterministic local data.
4. For real free providers, set `FINMIND_VN_PROVIDER=vnstock`,
   `FINMIND_XAUUSD_PROVIDER=yfinance`, `FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`,
   and `FINMIND_SJC_PROVIDER=sjc_official`.
5. Set `FINMIND_VNSTOCK_API_KEY` when `FINMIND_VN_PROVIDER=vnstock`.
6. Set `FINMIND_ALPHA_VANTAGE_API_KEY` only when the Alpha Vantage daily fallback is
   used.
7. Keep provider API keys server-side only.

Validation steps:

1. Log in as admin.
2. Open admin ingestion status.
3. Invoke the protected scheduled ingestion endpoint for `vn_prices`.
4. Trigger a manual fetch for `vn_prices`.
5. Trigger a manual fetch for `xauusd_prices`.
6. Trigger a manual fetch for `sjc_gold_prices`.
7. Re-run one fetch for the same period.
8. Attempt a second fetch for a dataset and period while the first matching job is queued or running.
9. Attempt `mode=historical` through the web API and verify it is rejected with instructions to use the backfill worker/script.
10. Run the independent VN historical backfill worker/script against the configured database:

   ```bash
   uv run python -m api.platform.ingestion.backfill \
     --source-id vn_prices \
     --from-date 2026-05-22 \
     --to-date 2026-06-22
   ```

11. Run the 1-month operator market-history plan for US and Gold-capable sources
    while VNStock historical backfill is paused:

   ```bash
   uv run python -m api.platform.ingestion.backfill \
     --preset market-history \
     --from-date 2026-05-22 \
     --to-date 2026-06-22
   ```

12. Run only the US 1-month daily base without triggering VN/gold providers:

   ```bash
   uv run python -m api.platform.ingestion.backfill \
     --preset us-daily-history \
     --from-date 2026-05-22 \
     --to-date 2026-06-22
   ```

Expected result: jobs show trigger type, status, timestamps, dataset scope, record counts, and non-secret diagnostics. The rerun does not create duplicate time-series records. The overlapping request returns blocked status with a clear message.

Real provider expected result: the default `market-history` plan attempts US daily
bars, XAUUSD daily fallback bars, and recent XAUUSD 1h bars for the 1-month
baseline. It does not call VNStock while VN historical backfill is paused. SJC
historical ranges are skipped until a historical archive is configured;
latest/current SJC quotes use `latest` or `period` fetches.

## Scenario 2: Market Data Inspection

1. Open the market data view.
2. Select a supported VN stock or gold dataset.
3. Filter the heatmap by a collection such as `VN30` and confirm the stock list and right-side rail stay scoped to the selected market.
4. Sort the stock list by change, volume, or sector.
5. Click a stock row or heatmap cell.
6. Switch the full instrument chart between `1h`, `4h`, `1d`, and `1M`.
7. Inspect the chart panel and table fallback.

Expected result: index mini charts, heatmap, sortable list, full instrument chart, table fallback, and freshness metadata are visible.
