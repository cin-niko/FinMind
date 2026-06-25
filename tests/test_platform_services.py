import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.platform.ingestion.demo_sources import DemoMarketDataSource
import api.platform.ingestion.free_sources as free_sources
from api.platform.ingestion import backfill as backfill_module
from api.platform.ingestion.backfill import (
    FREE_1H_WINDOW_DAYS,
    MARKET_HISTORY_PRESET,
    MARKET_LATEST_PRESET,
    ROADMAP_DISABLED_REASON,
    US_DAILY_HISTORY_PRESET,
    US_XAUUSD_HISTORY_PRESET,
    VN_HISTORY_PRESET,
    main as backfill_main,
    run_historical_backfill,
    run_market_history_backfill,
    run_market_latest_fetch,
    run_us_daily_history_backfill,
    run_us_xauusd_history_backfill,
    run_vn_history_backfill,
)
from api.platform.ingestion.free_sources import (
    AlphaVantageXauusdDailySource,
    SJCOfficialGoldSource,
    StooqUSStockDailySource,
    YFinanceUSStockSource,
    VnstockVNStockDailySource,
    VnstockVNStockSource,
    YFinanceXauusdSource,
    create_real_sources,
    _alpha_vantage_xauusd_daily_fetcher,
    _stooq_us_stock_daily_fetcher,
)
from api.platform.ingestion.service import (
    IngestionService,
    LazyFetchResult,
)
from api.platform.ingestion.errors import ProviderFetchError
from api.platform.ingestion.sources import TimeSeriesRecord
from api.platform.ingestion.store_writer import InMemoryTimeSeriesStore
from api.platform.ingestion.planner import IngestionFetchRequest, plan_fetch_periods
from api.platform.storage.postgres import PostgresTimeSeriesStore


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    app = create_app()
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login.status_code == 200
        yield test_client


def test_workflow_catalog_exposes_vn_stock_and_gold_workflows(
    client: TestClient,
) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    workflows = response.json()
    workflow_ids = {workflow["id"] for workflow in workflows}
    assert {
        "daily-market-brief",
        "vn-single-symbol-research",
        "gold-brief",
    } <= workflow_ids
    assert all(workflow["requires_citations"] for workflow in workflows)
    assert all("stages" in workflow for workflow in workflows)


def test_workflow_run_returns_cited_fresh_chart_result(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/daily-market-brief/run",
        json={"market": "VN_STOCK"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["kind"] == "workflow"
    assert result["status"] == "success"
    assert result["output"]["sections"][0]["citations"]
    assert result["output"]["citations"][0]["source_type"] == "market_data"
    assert result["output"]["freshness"][0]["status"] == "fresh"
    chart = result["output"]["artifacts"]["chart"]
    assert chart["artifact_type"] == "chart"
    assert chart["payload"]["series"]
    assert chart["evidence_refs"]
    assert "reasoning" not in str(result).lower()

    run_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert run_response.json() == result

    list_response = client.get("/api/runs")

    assert list_response.status_code == 200
    assert list_response.json()[0] == result


def test_market_overview_returns_filters_heatmap_and_sortable_rows(
    client: TestClient,
) -> None:
    response = client.get("/api/market/overview?market=VN&collection_id=vn30")

    assert response.status_code == 200
    overview = response.json()
    assert overview["selected_market"] == "VN"
    assert {"id": "vn30", "name": "VN30", "type": "index"} in overview["collections"]
    assert overview["watchlists"][0]["id"] == "watchlist:default-vn"
    assert [chart["symbol"] for chart in overview["index_charts"]] == [
        "VNINDEX",
        "VN100",
        "VN30",
        "HNXINDEX",
        "UPCOM",
    ]
    assert overview["heatmap"]
    assert overview["instrument_rows"]
    assert {cell["symbol"] for cell in overview["heatmap"]} == {"VCB", "VPB"}
    vpb = next(row for row in overview["instrument_rows"] if row["symbol"] == "VPB")
    assert vpb["sector"] == "Financials"
    assert vpb["industry"] == "Banking"
    assert "reasoning" not in str(overview).lower()


def test_instrument_chart_aggregates_stock_timeframes(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/market/instruments/vn_stock:VCB/chart?timeframe=4h",
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["instrument"]["symbol"] == "VCB"
    assert chart["timeframe"] == "4h"
    assert chart["freshness"]["status"] == "fresh"
    assert chart["records"] == [
        {
            "time": "2026-06-18T02:00:00+00:00",
            "open": 57400,
            "high": 58600,
            "low": 57300,
            "close": 58300,
            "volume": 1530000,
        },
        {
            "time": "2026-06-18T06:00:00+00:00",
            "open": 58300,
            "high": 58900,
            "low": 58100,
            "close": 58700,
            "volume": 1390000,
        },
    ]
    assert chart["table"][0]["time"] == "2026-06-18T02:00:00+00:00"


def test_market_overview_supports_us_market(
    client: TestClient,
) -> None:
    response = client.get("/api/market/overview?market=US")

    assert response.status_code == 200
    overview = response.json()
    assert overview["selected_market"] == "US"
    assert "US" in overview["available_markets"]
    assert {"id": "sp500", "name": "S&P 500", "type": "index"} in overview["collections"]
    assert [chart["symbol"] for chart in overview["index_charts"]] == [
        "S&P 500",
        "NASDAQ 100",
        "Dow",
        "Russell 2000",
        "VIX",
    ]
    row_symbols = {row["symbol"] for row in overview["instrument_rows"]}
    heatmap_symbols = {row["symbol"] for row in overview["heatmap"]}
    assert row_symbols >= {"AAPL", "MSFT", "NVDA"}
    assert heatmap_symbols >= {"AAPL", "MSFT", "NVDA"}
    assert row_symbols.isdisjoint({"SPY", "QQQ", "DIA", "IWM", "^VIX"})
    assert heatmap_symbols.isdisjoint({"SPY", "QQQ", "DIA", "IWM", "^VIX"})


def test_manual_ingestion_is_idempotent_and_updates_status(
    client: TestClient,
) -> None:
    first = client.post(
        "/api/admin/fetch",
        json={"source_id": "vn_prices", "period": "2026-06-18"},
    )
    second = client.post(
        "/api/admin/fetch",
        json={"source_id": "vn_prices", "period": "2026-06-18"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "success"
    assert second.json()["status"] == "success"
    assert first.json()["record_count"] == second.json()["record_count"]

    status = client.get("/api/admin/ingestion")
    assert status.status_code == 200
    payload = status.json()
    assert payload["jobs"][0]["trigger"] == "manual"
    assert payload["jobs"][0]["diagnostics"]["upserted"] == 6
    freshness = {
        item["dataset"]: item
        for item in payload["freshness"]
    }
    assert freshness["vn_prices"]["status"] in {"fresh", "stale"}
    assert freshness["vn_prices"]["record_count"] == 6
    assert set(freshness.keys()) == {"vn_prices_daily", "vn_prices"}

    records = client.get("/api/market-data/vn_prices")
    assert records.status_code == 200
    assert records.json()["record_count"] == 6


def test_worker_scheduled_ingestion_records_scheduled_trigger(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/worker/ingestion/scheduled",
        json={"source_id": "xauusd_prices", "period": "2026-06-18"},
    )

    assert response.status_code == 200
    assert response.json()["trigger"] == "scheduled"
    assert response.json()["status"] == "success"
    assert response.json()["record_count"] == 6


def test_worker_scheduled_ingestion_defaults_to_latest_mode(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/worker/ingestion/scheduled",
        json={"source_id": "sjc_gold_prices"},
    )

    assert response.status_code == 200
    assert response.json()["trigger"] == "scheduled"
    assert response.json()["status"] == "success"
    assert response.json()["diagnostics"]["mode"] == "latest"


def test_historical_fetch_planner_splits_inclusive_date_range() -> None:
    request = IngestionFetchRequest(
        source_id="vn_prices",
        mode="historical",
        from_date="2026-06-17",
        to_date="2026-06-19",
    )

    periods = plan_fetch_periods(
        request,
        now=datetime(2026, 6, 19, 8, tzinfo=UTC),
    )

    assert periods == ["2026-06-17", "2026-06-18", "2026-06-19"]


def test_latest_fetch_planner_resolves_current_date() -> None:
    request = IngestionFetchRequest(source_id="sjc_gold_prices", mode="latest")

    periods = plan_fetch_periods(
        request,
        now=datetime(2026, 6, 19, 8, tzinfo=UTC),
    )

    assert periods == ["2026-06-19"]


class RecordingSource:
    source_id = "vn_prices"

    def __init__(self) -> None:
        self.periods: list[str] = []

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        self.periods.append(period)
        period_start = period.split(":", maxsplit=1)[0]
        market_time = datetime.fromisoformat(period_start).replace(tzinfo=UTC)
        return [
            TimeSeriesRecord(
                dataset_id="vn_prices",
                record_key=f"vn_stock:VCB:{period}",
                instrument_id="vn_stock:VCB",
                market_time=market_time,
                collected_at=market_time,
                source_id="vnstock",
                payload={
                    "symbol": "VCB",
                    "exchange": "HOSE",
                    "interval_start": market_time.isoformat(),
                    "interval_end": market_time.isoformat(),
                    "open": 1,
                    "high": 1,
                    "low": 1,
                    "close": 1,
                    "volume": 1,
                    "currency": "VND",
                },
            )
        ]


def test_ingestion_service_runs_historical_range_through_single_pipeline() -> None:
    source = RecordingSource()
    service = IngestionService(
        sources={"vn_prices": source},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 19, 8, tzinfo=UTC),
    )

    job = service.run_manual_request(
        IngestionFetchRequest(
            source_id="vn_prices",
            mode="historical",
            from_date="2026-06-17",
            to_date="2026-06-18",
        )
    )

    assert job.status == "success"
    assert job.period == "2026-06-17:2026-06-18"
    assert job.record_count == 2
    assert job.diagnostics["periods"] == ["2026-06-17", "2026-06-18"]
    assert source.periods == ["2026-06-17", "2026-06-18"]


def test_historical_vn_backfill_records_partial_coverage_diagnostics() -> None:
    class PartialCoverageSource:
        source_id = "vn_prices"

        def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
            market_time = datetime.fromisoformat(period).replace(tzinfo=UTC)
            return [
                TimeSeriesRecord(
                    dataset_id="vn_prices",
                    record_key=f"vn_stock:VCB:{period}",
                    instrument_id="vn_stock:VCB",
                    market_time=market_time,
                    collected_at=market_time,
                    source_id="vnstock",
                    payload={
                        "symbol": "VCB",
                        "exchange": "HOSE",
                        "interval_start": market_time.isoformat(),
                        "interval_end": market_time.isoformat(),
                        "open": 1,
                        "high": 1,
                        "low": 1,
                        "close": 1,
                        "volume": 1,
                        "currency": "VND",
                        "capabilities": {
                            "provider": "vnstock",
                            "interval": "1h",
                            "requested_from": "2006-06-17",
                            "requested_to": "2026-06-18",
                            "covered_from": period,
                            "covered_to": period,
                            "coverage": "partial",
                            "missing_ranges": ["2006-06-17:2026-06-16"],
                        },
                    },
                )
            ]

    service = IngestionService(
        sources={"vn_prices": PartialCoverageSource()},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 19, 8, tzinfo=UTC),
    )

    job = service.run_manual_request(
        IngestionFetchRequest(
            source_id="vn_prices",
            mode="historical",
            from_date="2026-06-17",
            to_date="2026-06-18",
        )
    )

    assert job.status == "success"
    assert job.diagnostics["coverage"]["status"] == "partial"
    assert job.diagnostics["coverage"]["interval"] == "1h"
    assert job.diagnostics["coverage"]["provider"] == "vnstock"
    assert job.diagnostics["coverage"]["missing_ranges"] == ["2006-06-17:2026-06-16"]
    assert "api_key" not in str(job.diagnostics).lower()


def test_admin_manual_fetch_accepts_historical_range(client: TestClient) -> None:
    response = client.post(
        "/api/admin/fetch",
        json={
            "source_id": "vn_prices",
            "mode": "historical",
            "from_date": "2026-06-17",
            "to_date": "2026-06-18",
        },
    )

    assert response.status_code == 400
    assert "backfill worker" in response.json()["detail"]


def test_independent_backfill_runner_executes_historical_range() -> None:
    source = RecordingSource()
    service = IngestionService(
        sources={"vn_prices": source},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 19, 8, tzinfo=UTC),
    )

    job = run_historical_backfill(
        service=service,
        source_id="vn_prices",
        from_date="2026-06-17",
        to_date="2026-06-18",
    )

    assert job.status == "success"
    assert job.trigger == "backfill"
    assert job.period == "2026-06-17:2026-06-18"
    assert job.diagnostics["mode"] == "historical"
    assert source.periods == ["2026-06-17", "2026-06-18"]


def test_market_history_backfill_plan_uses_free_source_limits() -> None:
    sources = {
        "us_prices_daily": RecordingSource(),
        "vn_prices": RecordingSource(),
        "xauusd_prices": RecordingSource(),
        "xauusd_prices_daily": RecordingSource(),
        "sjc_gold_prices": RecordingSource(),
    }
    service = IngestionService(
        sources=sources,
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    results = run_market_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    by_source = {result.source_id: result for result in results}
    assert by_source["us_prices_daily"].status == "success"
    assert by_source["us_prices_daily"].from_date == "2026-06-18"
    assert by_source["us_prices_daily"].to_date == "2026-06-25"
    assert by_source["xauusd_prices_daily"].status == "success"
    assert by_source["xauusd_prices_daily"].from_date == "2026-06-18"
    assert by_source["xauusd_prices_daily"].to_date == "2026-06-25"
    assert by_source["xauusd_prices"].status == "success"
    assert by_source["xauusd_prices"].from_date == "2026-06-18"
    assert by_source["xauusd_prices"].to_date == "2026-06-25"
    assert by_source["sjc_gold_prices"].status == "skipped"
    assert by_source["sjc_gold_prices"].reason
    assert "current quote" in by_source["sjc_gold_prices"].reason
    assert sources["us_prices_daily"].periods == ["2026-06-18:2026-06-25"]
    assert sources["xauusd_prices_daily"].periods == ["2026-06-18:2026-06-25"]
    assert sources["xauusd_prices"].periods[0] == "2026-06-18"
    assert sources["vn_prices"].periods == []
    assert sources["sjc_gold_prices"].periods == []


def test_market_latest_fetch_runs_current_us_gold_sources_only() -> None:
    sources = {
        "us_prices": RecordingSource(),
        "vn_prices": RecordingSource(),
        "xauusd_prices": RecordingSource(),
        "sjc_gold_prices": RecordingSource(),
    }
    service = IngestionService(
        sources=sources,
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 25, 8, tzinfo=UTC),
    )

    results = run_market_latest_fetch(service=service)

    by_source = {result.source_id: result for result in results}
    assert set(by_source) == {"us_prices", "xauusd_prices", "sjc_gold_prices"}
    assert by_source["us_prices"].status == "success"
    assert by_source["xauusd_prices"].status == "success"
    assert by_source["sjc_gold_prices"].status == "success"
    assert by_source["us_prices"].from_date == "2026-06-25"
    assert by_source["us_prices"].to_date == "2026-06-25"
    assert sources["us_prices"].periods == ["2026-06-25"]
    assert sources["xauusd_prices"].periods == ["2026-06-25"]
    assert sources["sjc_gold_prices"].periods == ["2026-06-25"]
    assert sources["vn_prices"].periods == []


def test_us_daily_history_backfill_runs_only_us_daily_range_once() -> None:
    class RangeRecordingSource(RecordingSource):
        def __init__(self, source_id: str) -> None:
            super().__init__()
            self.source_id = source_id

        def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
            self.periods.append(period)
            market_time = datetime(2026, 5, 22, tzinfo=UTC)
            return [
                TimeSeriesRecord(
                    dataset_id="us_prices_daily",
                    record_key="us_stock:AAPL:2026-06-18",
                    instrument_id="us_stock:AAPL",
                    market_time=market_time,
                    collected_at=market_time,
                    source_id="stooq",
                    payload={
                        "market": "US_STOCK",
                        "symbol": "AAPL",
                        "exchange": "NASDAQ",
                        "trading_date": "2026-06-18",
                        "open": 2.1,
                        "high": 2.2,
                        "low": 2.0,
                        "close": 2.15,
                        "volume": 100000000,
                        "currency": "USD",
                    },
                )
            ]

    sources = {
        "us_prices_daily": RangeRecordingSource("us_prices_daily"),
        "vn_prices": RecordingSource(),
        "xauusd_prices": RecordingSource(),
    }
    service = IngestionService(
        sources=sources,
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    result = run_us_daily_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    assert result.source_id == "us_prices_daily"
    assert result.status == "success"
    assert result.from_date == "2026-06-18"
    assert result.to_date == "2026-06-25"
    assert result.job is not None
    assert result.job.period == "2026-06-18:2026-06-25"
    assert result.job.trigger == "backfill"
    assert result.job.diagnostics["mode"] == "historical_range"
    assert sources["us_prices_daily"].periods == ["2026-06-18:2026-06-25"]
    assert sources["vn_prices"].periods == []
    assert sources["xauusd_prices"].periods == []


def test_us_xauusd_history_backfill_runs_only_us_and_xauusd_sources() -> None:
    class RangeRecordingSource(RecordingSource):
        def __init__(self, source_id: str) -> None:
            super().__init__()
            self.source_id = source_id

        def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
            self.periods.append(period)
            market_time = datetime(2026, 5, 22, tzinfo=UTC)
            return [
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"{self.source_id}:2026-06-18",
                    instrument_id=self.source_id,
                    market_time=market_time,
                    collected_at=market_time,
                    source_id=self.source_id,
                    payload={},
                )
            ]

    sources = {
        "us_prices": RecordingSource(),
        "us_prices_daily": RangeRecordingSource("us_prices_daily"),
        "xauusd_prices": RecordingSource(),
        "xauusd_prices_daily": RangeRecordingSource("xauusd_prices_daily"),
        "vn_prices": RecordingSource(),
        "sjc_gold_prices": RecordingSource(),
    }
    service = IngestionService(
        sources=sources,
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    results = run_us_xauusd_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    by_source = {result.source_id: result for result in results}
    assert set(by_source) == {
        "us_prices_daily",
        "us_prices",
        "xauusd_prices_daily",
        "xauusd_prices",
    }
    assert by_source["us_prices_daily"].status == "success"
    assert by_source["us_prices_daily"].from_date == "2026-06-18"
    assert by_source["us_prices_daily"].to_date == "2026-06-25"
    assert by_source["us_prices"].from_date == "2026-06-18"
    assert by_source["us_prices"].to_date == "2026-06-25"
    assert by_source["xauusd_prices_daily"].from_date == "2026-06-18"
    assert by_source["xauusd_prices_daily"].to_date == "2026-06-25"
    assert by_source["xauusd_prices"].from_date == "2026-06-18"
    assert by_source["xauusd_prices"].to_date == "2026-06-25"
    assert sources["us_prices_daily"].periods == ["2026-06-18:2026-06-25"]
    assert sources["xauusd_prices_daily"].periods == ["2026-06-18:2026-06-25"]
    assert sources["us_prices"].periods[0] == "2026-06-18"
    assert sources["xauusd_prices"].periods[0] == "2026-06-18"
    assert sources["vn_prices"].periods == []
    assert sources["sjc_gold_prices"].periods == []


def test_ingestion_service_blocks_overlapping_dataset_period() -> None:
    store = InMemoryTimeSeriesStore()
    service = IngestionService(
        sources={"vn_prices": DemoMarketDataSource("vn_prices")},
        store=store,
    )
    store.create_running_job(source_id="vn_prices", period="2026-06-18", trigger="manual")

    blocked = service.run_manual(source_id="vn_prices", period="2026-06-18")

    assert blocked.status == "blocked"
    assert blocked.record_count == 0
    assert "already running" in blocked.diagnostics["message"]


def test_create_real_sources_returns_supported_dataset_adapters() -> None:
    sources = create_real_sources()

    assert set(sources) == {
        "us_prices",
        "us_prices_daily",
        "vn_prices",
        "vn_prices_daily",
        "xauusd_prices",
        "xauusd_prices_daily",
        "sjc_gold_prices",
    }
    assert sources["us_prices"].source_id == "us_prices"
    assert sources["us_prices"].provider == "yfinance"
    assert sources["us_prices_daily"].source_id == "us_prices_daily"
    assert sources["us_prices_daily"].provider == "stooq"
    assert sources["vn_prices"].source_id == "vn_prices"
    assert sources["vn_prices"].provider == "vnstock"
    assert sources["xauusd_prices"].provider == "yfinance"
    assert sources["xauusd_prices_daily"].provider == "alpha_vantage"
    assert sources["sjc_gold_prices"].provider == "sjc_official"
    assert all(hasattr(source, "fetch") for source in sources.values())


def test_yfinance_us_stock_adapter_normalizes_us_stock_bars() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2026-06-18"
        return {
            "capabilities": {
                "interval": "1h",
                "history": "recent",
                "max_intraday_days": 60,
            },
            "records": [
                {
                    "instrument_id": "us_stock:SPY",
                    "symbol": "SPY",
                    "exchange": "NYSEARCA",
                    "interval_start": "2026-06-18T14:00:00+00:00",
                    "interval_end": "2026-06-18T15:00:00+00:00",
                    "open": 548.1,
                    "high": 551.2,
                    "low": 547.8,
                    "close": 550.4,
                    "volume": 1200000,
                    "currency": "USD",
                    "sector": "Index ETF",
                    "industry": "Broad Market",
                }
            ],
        }

    source = YFinanceUSStockSource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "us_prices"
    assert record.source_id == "yfinance"
    assert record.record_key == "us_stock:SPY:2026-06-18T14:00:00+00:00"
    assert record.instrument_id == "us_stock:SPY"
    assert record.payload["market"] == "US_STOCK"
    assert record.payload["symbol"] == "SPY"
    assert record.payload["close"] == 550.4
    assert record.payload["capabilities"]["max_intraday_days"] == 60


def test_stooq_us_stock_daily_adapter_normalizes_daily_bars() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2026-06-18:2026-06-25"
        return {
            "capabilities": {
                "interval": "1d",
                "history": "1m",
                "provider": "stooq",
            },
            "records": [
                {
                    "instrument_id": "us_stock:AAPL",
                    "symbol": "AAPL",
                    "exchange": "NASDAQ",
                    "trading_date": "2026-06-18",
                    "open": 2.1,
                    "high": 2.2,
                    "low": 2.0,
                    "close": 2.15,
                    "volume": 100000000,
                    "currency": "USD",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                }
            ],
        }

    source = StooqUSStockDailySource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18:2026-06-25")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "us_prices_daily"
    assert record.source_id == "stooq"
    assert record.record_key == "us_stock:AAPL:2026-06-18"
    assert record.instrument_id == "us_stock:AAPL"
    assert record.market_time == datetime(2026, 6, 18, tzinfo=UTC)
    assert record.payload["market"] == "US_STOCK"
    assert record.payload["symbol"] == "AAPL"
    assert record.payload["close"] == 2.15
    assert record.payload["capabilities"]["history"] == "1m"


def test_stooq_fetcher_retries_transient_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    class FlakyResponse:
        text = "Date,Open,High,Low,Close,Volume\n2026-06-18,195,198,194,197,52000000\n"

        def raise_for_status(self) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                request = httpx.Request("GET", "https://stooq.com/q/d/l/")
                response = httpx.Response(429, request=request)
                raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, _url: str, params: dict[str, str]) -> FlakyResponse:
            assert params["s"] == "aapl.us"
            return FlakyResponse()

    monkeypatch.setattr(free_sources.httpx, "Client", FakeClient)
    monkeypatch.setattr(free_sources, "_provider_retry_sleep", lambda _attempt: None)
    fetch_json = _stooq_us_stock_daily_fetcher(("AAPL",), timeout_seconds=15)

    payload = fetch_json("2026-06-18:2026-06-18")

    assert calls == 2
    assert len(payload["records"]) == 1


def test_demo_us_daily_source_accepts_historical_range_scope() -> None:
    source = DemoMarketDataSource("us_prices_daily")

    records = source.fetch("2026-06-18:2026-06-25")

    assert records
    assert {record.dataset_id for record in records} == {"us_prices_daily"}
    assert records[0].market_time == datetime(2026, 6, 18, tzinfo=UTC)


def test_vnstock_adapter_normalizes_vn_stock_bars() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2026-06-18"
        return {
            "capabilities": {
                "interval": "1h",
                "from": "2026-06-18",
                "to": "2026-06-18",
                "rate_limit": "free-tier",
            },
            "records": [
                {
                    "symbol": "VCB",
                    "instrument_id": "vn_stock:VCB",
                    "exchange": "HOSE",
                    "interval_start": "2026-06-18T02:00:00+00:00",
                    "interval_end": "2026-06-18T03:00:00+00:00",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 390000,
                    "value": 22737000000,
                    "currency": "VND",
                    "sector": "Financials",
                    "industry": "Banking",
                }
            ],
        }

    source = VnstockVNStockSource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "vn_prices"
    assert record.source_id == "vnstock"
    assert record.record_key == "vn_stock:VCB:2026-06-18T02:00:00+00:00"
    assert record.market_time == datetime(2026, 6, 18, 2, tzinfo=UTC)
    assert record.payload["symbol"] == "VCB"
    assert record.payload["exchange"] == "HOSE"
    assert record.payload["close"] == 58300
    assert record.payload["value"] == 22737000000
    assert record.payload["capabilities"] == {
        "interval": "1h",
        "from": "2026-06-18",
        "to": "2026-06-18",
        "rate_limit": "free-tier",
    }


def test_vnstock_fetcher_uses_quote_api(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeQuote:
        def __init__(
            self,
            source: str,
            symbol: str,
            random_agent: bool,
            show_log: bool,
        ) -> None:
            calls.append(
                {
                    "source": source,
                    "symbol": symbol,
                    "random_agent": random_agent,
                    "show_log": show_log,
                }
            )

        def history(self, start: str, end: str, interval: str) -> list[dict[str, object]]:
            calls.append({"start": start, "end": end, "interval": interval})
            return [
                {
                    "time": "2026-06-18T02:00:00+00:00",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 390000,
                }
            ]

    monkeypatch.setattr(free_sources, "_vnstock_quote_class", lambda: FakeQuote)

    source = VnstockVNStockSource(api_key="vnstock-key", symbols=("VCB",))

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    assert records[0].record_key == "vn_stock:VCB:2026-06-18T02:00:00+00:00"
    assert calls == [
        {
            "source": "VCI",
            "symbol": "VCB",
            "random_agent": False,
            "show_log": False,
        },
        {"start": "2026-06-18", "end": "2026-06-19", "interval": "1H"},
    ]


def test_ingestion_service_records_provider_system_exit_as_failed_job() -> None:
    class ExitingSource:
        source_id = "vn_prices"

        def fetch(
            self,
            _period: str,
            *,
            instrument_id: str | None = None,
        ) -> list[TimeSeriesRecord]:
            raise SystemExit("Rate limit exceeded. raw provider details")

    service = IngestionService(
        sources={"vn_prices": ExitingSource()},
        store=InMemoryTimeSeriesStore(),
    )

    job = service.run_manual(source_id="vn_prices", period="2026-06-18")

    assert job.status == "failed"
    assert job.record_count == 0
    assert job.diagnostics["error"] == "Provider fetch failed: rate limit exceeded"


def test_market_data_expands_xauusd_daily_fallback_to_hourly_display_bars() -> None:
    store = InMemoryTimeSeriesStore(roadmap_markets_enabled=True)
    daily_record = TimeSeriesRecord(
        dataset_id="xauusd_prices_daily",
        record_key="gold:XAUUSD:2026-06-18",
        instrument_id="gold:XAUUSD",
        market_time=datetime(2026, 6, 18, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
        source_id="alpha_vantage",
        payload={
            "symbol": "XAUUSD",
            "trading_date": "2026-06-18",
            "open": 2320,
            "high": 2332,
            "low": 2315,
            "close": 2329,
            "unit": "oz",
            "currency": "USD",
            "fallback": "daily",
        },
    )
    store.upsert_many([daily_record])
    service = IngestionService(sources={}, store=store)

    payload = service.market_data("xauusd_prices")

    assert payload["record_count"] == 24
    first = payload["records"][0]
    last = payload["records"][-1]
    assert first["market_time"] == "2026-06-18T00:00:00+00:00"
    assert last["market_time"] == "2026-06-18T23:00:00+00:00"
    assert first["open"] == 2329
    assert first["high"] == 2329
    assert first["low"] == 2329
    assert first["close"] == 2329
    assert first["display_fallback"] is True
    assert first["source_grain"] == "1d"
    assert first["fallback_record_key"] == "gold:XAUUSD:2026-06-18"
    assert first["source_id"] == "alpha_vantage"


def test_market_data_prefers_real_xauusd_hourly_bar_over_daily_fallback() -> None:
    store = InMemoryTimeSeriesStore(roadmap_markets_enabled=True)
    hourly_record = TimeSeriesRecord(
        dataset_id="xauusd_prices",
        record_key="gold:XAUUSD:2026-06-18T02:00:00+00:00",
        instrument_id="gold:XAUUSD",
        market_time=datetime(2026, 6, 18, 2, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
        source_id="yfinance",
        payload={
            "symbol": "XAUUSD",
            "interval_start": "2026-06-18T02:00:00+00:00",
            "interval_end": "2026-06-18T03:00:00+00:00",
            "open": 2320,
            "high": 2325,
            "low": 2318,
            "close": 2324,
            "unit": "oz",
            "currency": "USD",
        },
    )
    daily_record = TimeSeriesRecord(
        dataset_id="xauusd_prices_daily",
        record_key="gold:XAUUSD:2026-06-18",
        instrument_id="gold:XAUUSD",
        market_time=datetime(2026, 6, 18, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
        source_id="alpha_vantage",
        payload={
            "symbol": "XAUUSD",
            "trading_date": "2026-06-18",
            "open": 2320,
            "high": 2332,
            "low": 2315,
            "close": 2329,
            "unit": "oz",
            "currency": "USD",
        },
    )
    store.upsert_many([hourly_record, daily_record])
    service = IngestionService(sources={}, store=store)

    payload = service.market_data("xauusd_prices")

    assert payload["record_count"] == 24
    two_am = next(
        record
        for record in payload["records"]
        if record["market_time"] == "2026-06-18T02:00:00+00:00"
    )
    assert two_am["source_id"] == "yfinance"
    assert two_am["close"] == 2324
    assert "display_fallback" not in two_am


def test_yfinance_adapter_normalizes_recent_xauusd_hourly_bars() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2026-06-18"
        return {
            "capabilities": {
                "interval": "1h",
                "history": "recent",
                "max_intraday_days": 60,
            },
            "records": [
                {
                    "interval_start": "2026-06-18T02:00:00+00:00",
                    "interval_end": "2026-06-18T03:00:00+00:00",
                    "open": 2320,
                    "high": 2325,
                    "low": 2318,
                    "close": 2324,
                }
            ],
        }

    source = YFinanceXauusdSource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "xauusd_prices"
    assert record.source_id == "yfinance"
    assert record.record_key == "gold:XAUUSD:2026-06-18T02:00:00+00:00"
    assert record.payload["symbol"] == "XAUUSD"
    assert record.payload["unit"] == "oz"
    assert record.payload["currency"] == "USD"
    assert record.payload["capabilities"]["max_intraday_days"] == 60


def test_alpha_vantage_adapter_normalizes_xauusd_daily_fallback() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2020-01-01:2026-06-18"
        return {
            "capabilities": {
                "interval": "1d",
                "fallback_for": "xauusd_prices",
                "reason": "free 1h history unavailable",
            },
            "records": [
                {
                    "trading_date": "2026-06-18",
                    "open": 2320,
                    "high": 2332,
                    "low": 2315,
                    "close": 2329,
                }
            ],
        }

    source = AlphaVantageXauusdDailySource(fetch_json=fetch_json)

    records = source.fetch("2020-01-01:2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "xauusd_prices_daily"
    assert record.source_id == "alpha_vantage"
    assert record.record_key == "gold:XAUUSD:2026-06-18"
    assert record.payload["fallback"] == "daily"
    assert record.payload["capabilities"]["fallback_for"] == "xauusd_prices"


def test_alpha_vantage_adapter_filters_daily_fallback_to_requested_range() -> None:
    def fetch_json(_period: str) -> dict[str, object]:
        return {
            "capabilities": {
                "interval": "1d",
                "fallback_for": "xauusd_prices",
                "reason": "free 1h history unavailable",
            },
            "records": [
                {
                    "trading_date": "2026-06-17",
                    "open": 2300,
                    "high": 2310,
                    "low": 2290,
                    "close": 2305,
                },
                {
                    "trading_date": "2026-06-18",
                    "open": 2320,
                    "high": 2332,
                    "low": 2315,
                    "close": 2329,
                },
                {
                    "trading_date": "2026-06-25",
                    "open": 2340,
                    "high": 2350,
                    "low": 2330,
                    "close": 2345,
                },
            ],
        }

    source = AlphaVantageXauusdDailySource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18:2026-06-25")

    assert [record.record_key for record in records] == [
        "gold:XAUUSD:2026-06-18",
        "gold:XAUUSD:2026-06-25",
    ]


def test_alpha_vantage_fetcher_uses_free_compact_daily_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "Time Series (Daily)": {
                    "2026-06-18": {
                        "1. open": "2320",
                        "2. high": "2332",
                        "3. low": "2315",
                        "4. close": "2329",
                    }
                }
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str, params: dict[str, object]) -> FakeResponse:
            captured["url"] = url
            captured["params"] = params
            return FakeResponse()

    monkeypatch.setattr(free_sources.httpx, "Client", FakeClient)

    fetch_json = _alpha_vantage_xauusd_daily_fetcher("alpha-key", timeout_seconds=12)
    payload = fetch_json("2026-06-18:2026-06-25")

    assert captured["params"] == {
        "function": "TIME_SERIES_DAILY",
        "symbol": "GLD",
        "outputsize": "compact",
        "apikey": "alpha-key",
    }
    assert payload["records"]


def test_alpha_vantage_daily_fallback_fails_empty_history() -> None:
    source = AlphaVantageXauusdDailySource(
        fetch_json=lambda _period: {
            "capabilities": {
                "interval": "1d",
                "fallback_for": "xauusd_prices",
            },
            "records": [],
        }
    )

    with pytest.raises(ProviderFetchError, match="no daily records"):
        source.fetch("2026-06-18:2026-06-25")


def test_sjc_adapter_parses_daily_quote_without_raw_page_dump() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><th>Loai vang</th><th>Mua vao</th><th>Ban ra</th></tr>
          <tr><td>SJC</td><td>76,400,000</td><td>78,600,000</td></tr>
        </table>
      </body>
    </html>
    """

    def fetch_json(period: str) -> str:
        assert period == "2026-06-18"
        return html

    source = SJCOfficialGoldSource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "sjc_gold_prices"
    assert record.source_id == "sjc_official"
    assert record.record_key == "gold:SJC:buy_sell:2026-06-18"
    assert record.payload["buy_price"] == 76400000
    assert record.payload["sell_price"] == 78600000
    assert record.payload["attribution"] == "SJC official"
    assert "<html>" not in str(record.payload)
    assert "76,400,000" not in str(record.payload)


class RecordingCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict[str, Any] | None]] = []

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, statement: str, params: dict[str, Any] | None = None) -> None:
        self.statements.append((statement, params))

    def fetchall(self) -> list[dict[str, Any]]:
        return []


class RecordingConnection:
    def __init__(self) -> None:
        self.cursor_instance = RecordingCursor()
        self.commits = 0
        self.closed = False

    def cursor(self) -> RecordingCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed = True


def test_postgres_store_upserts_records_into_typed_timeseries_tables() -> None:
    connection = RecordingConnection()
    store = PostgresTimeSeriesStore(connection_factory=lambda: connection)
    records = [
        TimeSeriesRecord(
            dataset_id="us_prices",
            record_key="us_stock:SPY:2026-06-18T14:00:00+00:00",
            instrument_id="us_stock:SPY",
            market_time=datetime(2026, 6, 18, 14, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 20, 30, tzinfo=UTC),
            source_id="yfinance",
            payload={
                "market": "US_STOCK",
                "symbol": "SPY",
                "exchange": "NYSEARCA",
                "interval_start": "2026-06-18T14:00:00+00:00",
                "interval_end": "2026-06-18T15:00:00+00:00",
                "open": 548.1,
                "high": 551.2,
                "low": 547.8,
                "close": 550.4,
                "volume": 1200000,
                "currency": "USD",
            },
        ),
        TimeSeriesRecord(
            dataset_id="us_prices_daily",
            record_key="us_stock:AAPL:2026-06-18",
            instrument_id="us_stock:AAPL",
            market_time=datetime(2026, 6, 18, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 20, 30, tzinfo=UTC),
            source_id="yfinance",
            payload={
                "market": "US_STOCK",
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "trading_date": "2026-06-18",
                "open": 195.0,
                "high": 198.0,
                "low": 194.5,
                "close": 197.2,
                "volume": 52000000,
                "currency": "USD",
            },
        ),
        TimeSeriesRecord(
            dataset_id="vn_prices",
            record_key="vn_stock:VCB:2026-06-18T02:00:00+00:00",
            instrument_id="vn_stock:VCB",
            market_time=datetime(2026, 6, 18, 2, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
            source_id="vn_prices",
            payload={
                "symbol": "VCB",
                "exchange": "HOSE",
                "interval_start": "2026-06-18T02:00:00+00:00",
                "interval_end": "2026-06-18T03:00:00+00:00",
                "open": 57400,
                "high": 58600,
                "low": 57300,
                "close": 58300,
                "volume": 390000,
                "currency": "VND",
            },
        ),
        TimeSeriesRecord(
            dataset_id="xauusd_prices",
            record_key="gold:XAUUSD:2026-06-18T02:00:00+00:00",
            instrument_id="gold:XAUUSD",
            market_time=datetime(2026, 6, 18, 2, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
            source_id="xauusd_prices",
            payload={
                "symbol": "XAUUSD",
                "interval_start": "2026-06-18T02:00:00+00:00",
                "interval_end": "2026-06-18T03:00:00+00:00",
                "open": 2320,
                "high": 2325,
                "low": 2318,
                "close": 2324,
                "unit": "oz",
                "currency": "USD",
            },
        ),
        TimeSeriesRecord(
            dataset_id="sjc_gold_prices",
            record_key="gold:SJC:buy_sell:2026-06-18",
            instrument_id="gold:SJC",
            market_time=datetime(2026, 6, 18, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
            source_id="sjc_gold_prices",
            payload={
                "symbol": "SJC",
                "quote_type": "buy_sell",
                "quote_date": "2026-06-18",
                "buy_price": 76400000,
                "sell_price": 78600000,
                "unit": "tael",
                "currency": "VND",
                "location": "VN",
            },
        ),
        TimeSeriesRecord(
            dataset_id="xauusd_prices_daily",
            record_key="gold:XAUUSD:2026-06-18",
            instrument_id="gold:XAUUSD",
            market_time=datetime(2026, 6, 18, tzinfo=UTC),
            collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
            source_id="alpha_vantage",
            payload={
                "symbol": "XAUUSD",
                "trading_date": "2026-06-18",
                "open": 2320,
                "high": 2332,
                "low": 2315,
                "close": 2329,
                "unit": "oz",
                "currency": "USD",
            },
        ),
    ]

    upserted = store.upsert_many(records)

    statements = "\n".join(
        statement
        for statement, _params in connection.cursor_instance.statements
    )
    assert upserted == 6
    assert "INSERT INTO stock_1h_bars" in statements
    assert "INSERT INTO stock_daily_bars" in statements
    assert "INSERT INTO xauusd_1h_bars" in statements
    assert "INSERT INTO xauusd_daily_bars" in statements
    assert "INSERT INTO sjc_gold_daily_quotes" in statements
    assert statements.count("ON CONFLICT") >= 3
    assert connection.commits == 1
    assert connection.closed


def test_postgres_store_upserts_vn_prices_daily_records() -> None:
    connection = RecordingConnection()
    store = PostgresTimeSeriesStore(connection_factory=lambda: connection)
    record = TimeSeriesRecord(
        dataset_id="vn_prices_daily",
        record_key="vn_stock:VCB:2026-06-18",
        instrument_id="vn_stock:VCB",
        market_time=datetime(2026, 6, 18, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 30, tzinfo=UTC),
        source_id="vnstock",
        payload={
            "market": "VN_STOCK",
            "symbol": "VCB",
            "exchange": "HOSE",
            "trade_date": "2026-06-18",
            "open": 57400,
            "high": 58600,
            "low": 57300,
            "close": 58300,
            "volume": 1530000,
            "currency": "VND",
        },
    )

    upserted = store.upsert_many([record, record])

    statements = "\n".join(
        statement
        for statement, _params in connection.cursor_instance.statements
    )
    assert upserted == 2
    assert "INSERT INTO vn_prices_daily" in statements
    assert (
        "ON CONFLICT (market, instrument_id, trade_date)" in statements
    )


def test_postgres_store_reads_vn_prices_daily_records() -> None:
    class ReadingCursor(RecordingCursor):
        def fetchall(self) -> list[dict[str, Any]]:
            if not self.statements:
                return []
            last_sql, _ = self.statements[-1]
            if "FROM vn_prices_daily" not in last_sql:
                return []
            return [
                {
                    "market": "VN_STOCK",
                    "instrument_id": "vn_stock:VCB",
                    "symbol": "VCB",
                    "exchange": "HOSE",
                    "trade_date": datetime(2026, 6, 18).date(),
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 1530000,
                    "value": None,
                    "currency": "VND",
                    "adjusted_close": None,
                    "corporate_action_flag": None,
                    "collected_at": datetime(
                        2026, 6, 18, 8, 30, tzinfo=UTC
                    ),
                    "source_id": "vnstock",
                    "freshness_status": "fresh",
                }
            ]

    class ReadingConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.cursor_instance = ReadingCursor()

    connection = ReadingConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )

    records = store.list_dataset("vn_prices_daily")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "vn_prices_daily"
    assert record.instrument_id == "vn_stock:VCB"
    assert record.payload["trade_date"] == "2026-06-18"
    assert record.payload["close"] == 58300


def test_vn_prices_daily_sql_migration_defines_typed_table() -> None:
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "api"
        / "platform"
        / "storage"
        / "sql"
        / "001_phase002_timeseries.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS vn_prices_daily" in migration
    assert "trade_date DATE NOT NULL" in migration
    assert (
        "PRIMARY KEY (market, instrument_id, trade_date)" in migration
    )
    assert (
        "CHECK (high >= open AND high >= low AND high >= close)"
        in migration
    )
    assert (
        "CHECK (low <= open AND low <= high AND low <= close)"
        in migration
    )
    assert (
        "create_hypertable('vn_prices_daily', 'trade_date'"
        in migration
    )


def test_single_symbol_workflow_targets_requested_symbol(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-single-symbol-research/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    section = result["output"]["sections"][0]
    chart = result["output"]["artifacts"]["chart"]

    assert result["inputs"]["symbol"] == "VCB"
    assert "VCB closed" in section["content"]
    assert "VNINDEX" not in section["content"]
    assert chart["payload"]["table"] == [
        {
            "record_key": "VCB-2026-06-18",
            "market_time": "2026-06-18T07:00:00+00:00",
            "close": 58200,
        }
    ]


def test_invalid_workflow_input_does_not_create_successful_run(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/daily-market-brief/run",
        json={"market": "US_STOCK"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "V1 supports VN stocks and gold" in detail


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"


def _vn100_csv_path() -> "Path":
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[1]
        / "data"
        / "seed"
        / "vn100.csv"
    )


def test_vn100_seed_csv_has_exactly_100_unique_hose_rows() -> None:
    from api.platform.ingestion.seed import parse_vn100_csv

    rows = parse_vn100_csv(_vn100_csv_path())

    assert len(rows) == 100
    symbols = [row.symbol for row in rows]
    assert len(set(symbols)) == 100
    assert all(row.exchange == "HOSE" for row in rows)
    assert all(row.currency == "VND" for row in rows)
    assert all(row.status == "active" for row in rows)
    assert all(row.symbol == row.symbol.upper() for row in rows)


def test_vn100_seed_loader_emits_expected_sql_and_counts() -> None:
    from api.platform.ingestion.seed import (
        VN100_COLLECTION_ID,
        VN100_EFFECTIVE_FROM,
        load_vn100_seed,
    )

    connection = RecordingConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )

    result = load_vn100_seed(_vn100_csv_path(), store)

    statements = connection.cursor_instance.statements
    instrument_stmts = [
        (sql, params)
        for sql, params in statements
        if "INSERT INTO market_instruments" in sql
    ]
    collection_stmts = [
        (sql, params)
        for sql, params in statements
        if "INSERT INTO market_collections" in sql
    ]
    membership_stmts = [
        (sql, params)
        for sql, params in statements
        if "INSERT INTO market_collection_memberships" in sql
    ]

    assert len(instrument_stmts) == 100
    assert len(collection_stmts) == 1
    assert len(membership_stmts) == 100

    assert result.instruments_seen == 100
    assert result.instruments_upserted == 100
    assert result.collection_upserted == 1
    assert result.memberships_seen == 100
    assert result.memberships_upserted == 100

    collection_params = collection_stmts[0][1]
    assert collection_params is not None
    assert collection_params["collection_id"] == VN100_COLLECTION_ID
    assert collection_params["market"] == "VN_STOCK"

    instrument_params = instrument_stmts[0][1]
    assert instrument_params is not None
    assert instrument_params["instrument_id"].startswith(
        "vn_stock:"
    )
    assert instrument_params["market"] == "VN_STOCK"
    assert instrument_params["asset_class"] == "stock"
    assert instrument_params["exchange"] == "HOSE"

    membership_params = membership_stmts[0][1]
    assert membership_params is not None
    assert membership_params["collection_id"] == VN100_COLLECTION_ID
    assert (
        membership_params["effective_from"] == VN100_EFFECTIVE_FROM
    )

    instrument_sql = instrument_stmts[0][0]
    assert "ON CONFLICT (instrument_id) DO UPDATE" in instrument_sql
    assert "symbol = EXCLUDED.symbol" not in instrument_sql
    assert "display_name = EXCLUDED.display_name" in instrument_sql

    collection_sql = collection_stmts[0][0]
    assert (
        "ON CONFLICT (market, collection_id) DO NOTHING"
        in collection_sql
    )

    membership_sql = membership_stmts[0][0]
    assert (
        "ON CONFLICT (collection_id, instrument_id, effective_from)"
        " DO NOTHING" in membership_sql
    )

    assert connection.commits == 1
    assert connection.closed


def test_vn100_seed_loader_is_idempotent_on_the_wire() -> None:
    from api.platform.ingestion.seed import load_vn100_seed

    first_connection = RecordingConnection()
    first_store = PostgresTimeSeriesStore(
        connection_factory=lambda: first_connection
    )
    load_vn100_seed(_vn100_csv_path(), first_store)

    second_connection = RecordingConnection()
    second_store = PostgresTimeSeriesStore(
        connection_factory=lambda: second_connection
    )
    load_vn100_seed(_vn100_csv_path(), second_store)

    first = first_connection.cursor_instance.statements
    second = second_connection.cursor_instance.statements

    assert len(first) == len(second)
    for (sql_a, params_a), (sql_b, params_b) in zip(
        first, second, strict=True
    ):
        assert sql_a == sql_b
        assert params_a == params_b


def test_vn100_seed_module_exposes_main_entrypoint() -> None:
    from api.platform.ingestion import seed as seed_module

    assert callable(seed_module.main)
    assert hasattr(seed_module, "load_vn100_seed")
    assert hasattr(seed_module, "SeedResult")


def test_vnstock_daily_adapter_normalizes_vn_prices_daily() -> None:
    def fetch_json(period: str) -> dict[str, object]:
        assert period == "2026-06-18"
        return {
            "capabilities": {
                "interval": "1d",
                "provider": "vnstock",
                "coverage": "rolling",
                "from": "2026-06-18",
                "to": "2026-06-18",
            },
            "records": [
                {
                    "symbol": "VCB",
                    "instrument_id": "vn_stock:VCB",
                    "exchange": "HOSE",
                    "trade_date": "2026-06-18",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 1530000,
                    "value": 89215000000,
                    "currency": "VND",
                }
            ],
        }

    source = VnstockVNStockDailySource(fetch_json=fetch_json)

    records = source.fetch("2026-06-18")

    assert len(records) == 1
    record = records[0]
    assert record.dataset_id == "vn_prices_daily"
    assert record.source_id == "vnstock"
    assert record.instrument_id == "vn_stock:VCB"
    assert record.record_key == "vn_stock:VCB:2026-06-18"
    assert record.market_time == datetime(2026, 6, 18, tzinfo=UTC)
    assert record.payload["trade_date"] == "2026-06-18"
    assert record.payload["close"] == 58300
    assert record.payload["market"] == "VN_STOCK"
    assert "interval_start" not in record.payload
    assert record.payload["capabilities"]["interval"] == "1d"


def test_vnstock_daily_fetcher_uses_quote_api_with_1d_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class FakeQuote:
        def __init__(
            self,
            source: str,
            symbol: str,
            random_agent: bool,
            show_log: bool,
        ) -> None:
            calls.append(
                {
                    "source": source,
                    "symbol": symbol,
                    "random_agent": random_agent,
                    "show_log": show_log,
                }
            )

        def history(
            self, start: str, end: str, interval: str
        ) -> list[dict[str, object]]:
            calls.append(
                {"start": start, "end": end, "interval": interval}
            )
            return [
                {
                    "time": "2026-06-17",
                    "open": 56900,
                    "high": 57500,
                    "low": 56700,
                    "close": 57400,
                    "volume": 1410000,
                },
                {
                    "time": "2026-06-18",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 1530000,
                },
            ]

    monkeypatch.setattr(
        free_sources, "_vnstock_quote_class", lambda: FakeQuote
    )

    source = VnstockVNStockDailySource(
        api_key="vnstock-key", symbols=("VCB",)
    )

    records = source.fetch("2026-06-17:2026-06-18")

    assert len(records) == 2
    assert {r.record_key for r in records} == {
        "vn_stock:VCB:2026-06-17",
        "vn_stock:VCB:2026-06-18",
    }
    assert calls == [
        {
            "source": "VCI",
            "symbol": "VCB",
            "random_agent": False,
            "show_log": False,
        },
        {
            "start": "2026-06-17",
            "end": "2026-06-18",
            "interval": "1D",
        },
    ]


def test_vnstock_daily_records_persist_via_vn_prices_daily_upsert() -> (
    None
):
    def fetch_json(_period: str) -> dict[str, object]:
        return {
            "capabilities": {"interval": "1d", "provider": "vnstock"},
            "records": [
                {
                    "symbol": "VPB",
                    "instrument_id": "vn_stock:VPB",
                    "exchange": "HOSE",
                    "trade_date": "2026-06-18",
                    "open": 21400,
                    "high": 21800,
                    "low": 21200,
                    "close": 21700,
                    "volume": 5_120_000,
                    "currency": "VND",
                }
            ],
        }

    source = VnstockVNStockDailySource(fetch_json=fetch_json)
    records = source.fetch("2026-06-18")

    connection = RecordingConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )
    upserted = store.upsert_many(records)

    statements = "\n".join(
        statement
        for statement, _params in connection.cursor_instance.statements
    )
    assert upserted == 1
    assert "INSERT INTO vn_prices_daily" in statements
    assert (
        "ON CONFLICT (market, instrument_id, trade_date)" in statements
    )
    assert "INSERT INTO stock_1h_bars" not in statements


def test_vnstock_hourly_path_remains_unchanged_for_vn_prices() -> None:
    def hourly_fetch_json(_period: str) -> dict[str, object]:
        return {
            "capabilities": {"interval": "1h", "provider": "vnstock"},
            "records": [
                {
                    "symbol": "VCB",
                    "instrument_id": "vn_stock:VCB",
                    "exchange": "HOSE",
                    "interval_start": "2026-06-18T02:00:00+00:00",
                    "interval_end": "2026-06-18T03:00:00+00:00",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 390000,
                    "currency": "VND",
                }
            ],
        }

    hourly = VnstockVNStockSource(fetch_json=hourly_fetch_json)
    records = hourly.fetch("2026-06-18")

    assert len(records) == 1
    assert records[0].dataset_id == "vn_prices"
    assert "interval_start" in records[0].payload
    assert "trade_date" not in records[0].payload


def test_create_real_sources_registers_vn_prices_daily() -> None:
    sources = create_real_sources()

    assert "vn_prices_daily" in sources
    daily = sources["vn_prices_daily"]
    assert isinstance(daily, VnstockVNStockDailySource)
    assert daily.source_id == "vn_prices_daily"
    assert daily.provider == "vnstock"
    assert sources["vn_prices"].source_id == "vn_prices"


class VNDailyRangeSource:
    """Records `period` ranges as `vn_prices_daily` for tests."""

    source_id = "vn_prices_daily"

    def __init__(self) -> None:
        self.periods: list[str] = []

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        self.periods.append(period)
        market_time = datetime(2026, 6, 18, tzinfo=UTC)
        return [
            TimeSeriesRecord(
                dataset_id="vn_prices_daily",
                record_key="vn_stock:VCB:2026-06-18",
                instrument_id="vn_stock:VCB",
                market_time=market_time,
                collected_at=market_time,
                source_id="vnstock",
                payload={
                    "market": "VN_STOCK",
                    "symbol": "VCB",
                    "exchange": "HOSE",
                    "trade_date": "2026-06-18",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 1530000,
                    "currency": "VND",
                },
            )
        ]


def test_vn_history_preset_runs_daily_required_and_hourly_best_effort() -> (
    None
):
    daily = VNDailyRangeSource()
    hourly = RecordingSource()
    service = IngestionService(
        sources={"vn_prices_daily": daily, "vn_prices": hourly},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    results = run_vn_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    by_source = {result.source_id: result for result in results}
    assert set(by_source) == {"vn_prices_daily", "vn_prices"}
    assert by_source["vn_prices_daily"].status == "success"
    assert by_source["vn_prices_daily"].from_date == "2026-06-18"
    assert by_source["vn_prices_daily"].to_date == "2026-06-25"
    assert by_source["vn_prices_daily"].job is not None
    assert (
        by_source["vn_prices_daily"].job.diagnostics["mode"]
        == "historical_range"
    )
    assert daily.periods == ["2026-06-18:2026-06-25"]
    assert by_source["vn_prices"].status == "success"
    assert by_source["vn_prices"].from_date == "2026-06-18"
    assert by_source["vn_prices"].to_date == "2026-06-25"
    assert hourly.periods[0] == "2026-06-18"


def test_vn_history_preset_clamps_hourly_leg_to_free_1h_window() -> None:
    daily = VNDailyRangeSource()
    hourly = RecordingSource()
    service = IngestionService(
        sources={"vn_prices_daily": daily, "vn_prices": hourly},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    from_date = "2025-01-01"
    to_date = "2026-06-25"
    results = run_vn_history_backfill(
        service=service,
        from_date=from_date,
        to_date=to_date,
    )

    by_source = {result.source_id: result for result in results}
    assert by_source["vn_prices_daily"].from_date == from_date
    assert by_source["vn_prices_daily"].to_date == to_date
    expected_start = (
        datetime.fromisoformat(to_date).date()
        - timedelta(days=FREE_1H_WINDOW_DAYS - 1)
    )
    assert (
        by_source["vn_prices"].from_date == expected_start.isoformat()
    )
    assert by_source["vn_prices"].to_date == to_date


def test_vn_history_preset_skips_hourly_when_source_missing() -> None:
    daily = VNDailyRangeSource()
    service = IngestionService(
        sources={"vn_prices_daily": daily},
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    results = run_vn_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    by_source = {result.source_id: result for result in results}
    assert by_source["vn_prices_daily"].status == "success"
    assert by_source["vn_prices"].status == "skipped"
    assert by_source["vn_prices"].reason
    assert "not configured" in by_source["vn_prices"].reason


def test_vn_history_preset_marks_hourly_failure_as_skipped() -> None:
    class FailingHourly:
        source_id = "vn_prices"

        def fetch(
            self,
            _period: str,
            *,
            instrument_id: str | None = None,
        ) -> list[TimeSeriesRecord]:
            raise ProviderFetchError("vnstock 1h rate limited")

    daily = VNDailyRangeSource()
    service = IngestionService(
        sources={
            "vn_prices_daily": daily,
            "vn_prices": FailingHourly(),
        },
        store=InMemoryTimeSeriesStore(),
        clock=lambda: datetime(2026, 6, 21, 8, tzinfo=UTC),
    )

    results = run_vn_history_backfill(
        service=service,
        from_date="2026-06-18",
        to_date="2026-06-25",
    )

    by_source = {result.source_id: result for result in results}
    assert by_source["vn_prices_daily"].status == "success"
    assert by_source["vn_prices"].status == "skipped"
    assert by_source["vn_prices"].reason
    assert "best-effort" in by_source["vn_prices"].reason


def _set_admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv(
        "FINMIND_SESSION_SECRET", "session-secret-with-length"
    )


@pytest.mark.parametrize(
    "preset, extra_args",
    (
        (MARKET_LATEST_PRESET, ()),
        (
            MARKET_HISTORY_PRESET,
            ("--from-date", "2026-06-18", "--to-date", "2026-06-25"),
        ),
        (
            US_DAILY_HISTORY_PRESET,
            ("--from-date", "2026-06-18", "--to-date", "2026-06-25"),
        ),
        (
            US_XAUUSD_HISTORY_PRESET,
            ("--from-date", "2026-06-18", "--to-date", "2026-06-25"),
        ),
    ),
)
def test_roadmap_presets_short_circuit_when_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    preset: str,
    extra_args: tuple[str, ...],
) -> None:
    _set_admin_env(monkeypatch)
    monkeypatch.delenv("FINMIND_ROADMAP_MARKETS", raising=False)

    def boom(*_a: object, **_kw: object) -> object:
        raise AssertionError(
            "roadmap runner must not be invoked when flag is disabled"
        )

    monkeypatch.setattr(backfill_module, "create_ingestion_service", boom)
    monkeypatch.setattr(backfill_module, "run_market_latest_fetch", boom)
    monkeypatch.setattr(
        backfill_module, "run_market_history_backfill", boom
    )
    monkeypatch.setattr(
        backfill_module, "run_us_daily_history_backfill", boom
    )
    monkeypatch.setattr(
        backfill_module, "run_us_xauusd_history_backfill", boom
    )

    exit_code = backfill_main(["--preset", preset, *extra_args])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["preset"] == preset
    assert payload["status"] == "skipped"
    assert payload["reason"] == ROADMAP_DISABLED_REASON


def test_roadmap_flag_enabled_invokes_underlying_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_admin_env(monkeypatch)
    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "true")

    monkeypatch.setattr(
        backfill_module,
        "create_ingestion_service",
        lambda _settings: "sentinel-service",
    )
    called: list[object] = []

    def fake_runner(*, service: object) -> list[object]:
        called.append(service)
        return []

    monkeypatch.setattr(
        backfill_module, "run_market_latest_fetch", fake_runner
    )

    exit_code = backfill_main(["--preset", MARKET_LATEST_PRESET])

    assert exit_code == 0
    assert called == ["sentinel-service"]
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["preset"] == MARKET_LATEST_PRESET
    assert payload["results"] == []


def test_vn_history_preset_main_dispatches_without_roadmap_flag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_admin_env(monkeypatch)
    monkeypatch.delenv("FINMIND_ROADMAP_MARKETS", raising=False)

    monkeypatch.setattr(
        backfill_module,
        "create_ingestion_service",
        lambda _settings: "sentinel-service",
    )
    captured: dict[str, object] = {}

    def fake_vn_runner(
        *,
        service: object,
        from_date: str,
        to_date: str,
    ) -> list[object]:
        captured["service"] = service
        captured["from"] = from_date
        captured["to"] = to_date
        return []

    monkeypatch.setattr(
        backfill_module, "run_vn_history_backfill", fake_vn_runner
    )

    exit_code = backfill_main(
        [
            "--preset",
            VN_HISTORY_PRESET,
            "--from-date",
            "2026-06-18",
            "--to-date",
            "2026-06-25",
        ]
    )

    assert exit_code == 0
    assert captured == {
        "service": "sentinel-service",
        "from": "2026-06-18",
        "to": "2026-06-25",
    }
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["preset"] == VN_HISTORY_PRESET
    assert payload["status"] == "success"


def test_settings_parses_roadmap_markets_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api.settings import Settings

    _set_admin_env(monkeypatch)
    monkeypatch.delenv("FINMIND_ROADMAP_MARKETS", raising=False)
    assert Settings.from_env().roadmap_markets_enabled is False

    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "TRUE")
    assert Settings.from_env().roadmap_markets_enabled is True

    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "1")
    assert Settings.from_env().roadmap_markets_enabled is True

    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "False")
    assert Settings.from_env().roadmap_markets_enabled is False

    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "0")
    assert Settings.from_env().roadmap_markets_enabled is False


class _LazyVNDailySource:
    """Records lazy fetch calls and returns deterministic vn daily rows."""

    source_id = "vn_prices_daily"

    def __init__(self) -> None:
        self.periods: list[str] = []
        self.instrument_ids: list[str | None] = []

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        self.periods.append(period)
        self.instrument_ids.append(instrument_id)
        symbol = (
            instrument_id.split(":", 1)[1]
            if instrument_id and instrument_id.startswith("vn_stock:")
            else "VCB"
        )
        resolved_id = f"vn_stock:{symbol}"
        market_time = datetime(2026, 6, 25, tzinfo=UTC)
        return [
            TimeSeriesRecord(
                dataset_id="vn_prices_daily",
                record_key=f"{resolved_id}:{period}",
                instrument_id=resolved_id,
                market_time=market_time,
                collected_at=market_time,
                source_id="vnstock",
                payload={
                    "market": "VN_STOCK",
                    "symbol": symbol,
                    "exchange": "HOSE",
                    "trade_date": "2026-06-25",
                    "open": 57400,
                    "high": 58600,
                    "low": 57300,
                    "close": 58300,
                    "volume": 1530000,
                    "currency": "VND",
                },
            )
        ]


def _lazy_service(
    source: _LazyVNDailySource | None = None,
    *,
    seed_membership: bool = True,
) -> tuple[IngestionService, InMemoryTimeSeriesStore, _LazyVNDailySource]:
    used_source = source or _LazyVNDailySource()
    store = InMemoryTimeSeriesStore()
    if seed_membership:
        store.collection_memberships.add(("VN100", "vn_stock:VCB"))
    service = IngestionService(
        sources={"vn_prices_daily": used_source},
        store=store,
        clock=lambda: datetime(2026, 6, 25, 8, tzinfo=UTC),
    )
    return service, store, used_source


def test_lazy_fetch_triggers_latest_and_period_for_vn100_first_access() -> (
    None
):
    service, store, source = _lazy_service()

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert isinstance(result, LazyFetchResult)
    assert result.status == "success"
    assert result.dataset_id == "vn_prices_daily"
    assert result.instrument_id == "vn_stock:VCB"
    assert [job.trigger for job in result.jobs] == ["lazy", "lazy"]
    assert [job.status for job in result.jobs] == ["success", "success"]
    modes = [job.diagnostics["mode"] for job in result.jobs]
    assert modes == ["latest", "period"]
    assert source.periods == ["2026-06-25", "2026-05-26:2026-06-25"]
    assert source.instrument_ids == [
        "vn_stock:VCB",
        "vn_stock:VCB",
    ]
    assert store.has_dataset_rows(
        "vn_prices_daily", "vn_stock:VCB"
    )
    serialized = result.to_dict()
    assert serialized["status"] == "success"
    assert len(serialized["jobs"]) == 2


def test_lazy_fetch_returns_already_present_when_rows_exist() -> None:
    service, store, source = _lazy_service()
    existing = TimeSeriesRecord(
        dataset_id="vn_prices_daily",
        record_key="vn_stock:VCB:2026-06-18",
        instrument_id="vn_stock:VCB",
        market_time=datetime(2026, 6, 18, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, tzinfo=UTC),
        source_id="vnstock",
        payload={"trade_date": "2026-06-18"},
    )
    store.records[(existing.dataset_id, existing.record_key)] = existing

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert result.status == "already_present"
    assert result.jobs == []
    assert source.periods == []


def test_lazy_fetch_rejects_out_of_universe_instrument() -> None:
    service, store, source = _lazy_service(seed_membership=False)

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:UNKNOWN",
    )

    assert result.status == "out_of_scope"
    assert result.reason
    assert "VN100" in result.reason or "universe" in result.reason
    assert result.jobs == []
    assert source.periods == []
    assert store.jobs == []
    assert all(
        record.instrument_id != "vn_stock:UNKNOWN"
        for record in store.records.values()
    )


def test_lazy_fetch_reports_blocked_when_overlap_guard_active() -> None:
    service, store, source = _lazy_service()
    store.create_running_job(
        source_id="vn_prices_daily",
        period="vn_stock:VCB:2026-06-25",
        trigger="scheduled",
    )

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert result.status == "blocked"
    assert source.periods == []
    assert len(result.jobs) == 1
    assert result.jobs[0].status == "blocked"


def test_lazy_fetch_never_triggers_historical_mode() -> None:
    class ModeRecordingSource(_LazyVNDailySource):
        def __init__(self) -> None:
            super().__init__()
            self.modes_observed: list[str] = []

    source = ModeRecordingSource()
    service, _store, _ = _lazy_service(source=source)

    captured_requests: list[IngestionFetchRequest] = []
    original = service._run_request

    def spy(request: IngestionFetchRequest, trigger: str) -> Any:
        captured_requests.append(request)
        return original(request=request, trigger=trigger)

    service._run_request = spy  # type: ignore[method-assign]
    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert result.status == "success"
    modes = [request.mode for request in captured_requests]
    assert modes == ["latest", "period"]
    assert "historical" not in modes


def test_lazy_fetch_rejects_unsupported_dataset() -> None:
    service, _store, source = _lazy_service()

    result = service.ensure_dataset_rows(
        dataset_id="us_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert result.status == "not_supported"
    assert result.reason
    assert "vn_prices_daily" in result.reason
    assert result.jobs == []
    assert source.periods == []


def test_lazy_fetch_passes_hpg_instrument_to_source() -> None:
    service, store, source = _lazy_service()
    store.collection_memberships.add(("VN100", "vn_stock:HPG"))

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:HPG",
    )

    assert result.status == "success"
    assert source.instrument_ids == ["vn_stock:HPG", "vn_stock:HPG"]
    assert store.has_dataset_rows("vn_prices_daily", "vn_stock:HPG")


def test_lazy_overlap_does_not_block_different_instruments() -> None:
    service, store, _source = _lazy_service()
    store.collection_memberships.add(("VN100", "vn_stock:FPT"))
    store.create_running_job(
        source_id="vn_prices_daily",
        period="vn_stock:HPG:2026-06-25",
        trigger="lazy",
    )

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:FPT",
    )

    assert result.status == "success"


def test_lazy_overlap_blocks_same_instrument() -> None:
    service, store, source = _lazy_service()
    store.create_running_job(
        source_id="vn_prices_daily",
        period="vn_stock:VCB:2026-06-25",
        trigger="lazy",
    )

    result = service.ensure_dataset_rows(
        dataset_id="vn_prices_daily",
        instrument_id="vn_stock:VCB",
    )

    assert result.status == "blocked"
    assert source.periods == []


def test_vnstock_daily_source_resolves_symbol_from_instrument_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, ...]] = []

    def spy_payload(
        period: str,
        symbols: tuple[str, ...],
        api_key: str | None,
    ) -> object:
        captured.append(symbols)
        return {
            "capabilities": {"interval": "1d", "provider": "vnstock"},
            "records": [],
        }

    monkeypatch.setattr(
        free_sources, "_vnstock_daily_payload", spy_payload
    )
    source = VnstockVNStockDailySource(symbols=("VCB", "VPB"))
    source.fetch("2026-06-25", instrument_id="vn_stock:HPG")
    source.fetch("2026-06-25")

    assert captured == [("HPG",), ("VCB", "VPB")]


def test_postgres_store_checks_collection_membership_and_dataset_rows() -> (
    None
):
    class MembershipCursor(RecordingCursor):
        def fetchall(self) -> list[dict[str, Any]]:
            if not self.statements:
                return []
            last_sql, params = self.statements[-1]
            if "market_collection_memberships" in last_sql:
                assert params == {
                    "collection_id": "VN100",
                    "instrument_id": "vn_stock:VCB",
                }
                return [{"?column?": 1}]
            if "FROM vn_prices_daily" in last_sql:
                assert params == {"instrument_id": "vn_stock:VCB"}
                return [{"?column?": 1}]
            return []

    class MembershipConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.cursor_instance = MembershipCursor()

    connection = MembershipConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )

    assert store.is_in_collection("VN100", "vn_stock:VCB") is True
    assert store.has_dataset_rows(
        "vn_prices_daily", "vn_stock:VCB"
    ) is True
    assert (
        store.has_dataset_rows("us_prices_daily", "vn_stock:VCB")
        is False
    )


# ---------------------------------------------------------------------------
# Canonical vn_prices_daily chart wiring (post-T046 fix)
# ---------------------------------------------------------------------------


from api.platform.ingestion.store_writer import InstrumentMetadata


def _vcb_metadata() -> InstrumentMetadata:
    return InstrumentMetadata(
        instrument_id="vn_stock:VCB",
        symbol="VCB",
        market="VN_STOCK",
        asset_class="stock",
        exchange="HOSE",
        display_name="Vietcombank",
        currency="VND",
        sector="Financials",
        industry="Banking",
        sub_industry="Commercial Banking",
    )


def _vn_daily_payload_record(
    instrument_id: str,
    trade_date_str: str,
    *,
    close: int,
) -> TimeSeriesRecord:
    market_time = datetime.fromisoformat(
        f"{trade_date_str}T00:00:00+00:00"
    )
    return TimeSeriesRecord(
        dataset_id="vn_prices_daily",
        record_key=f"{instrument_id}:{trade_date_str}",
        instrument_id=instrument_id,
        market_time=market_time,
        collected_at=market_time,
        source_id="vnstock",
        payload={
            "market": "VN_STOCK",
            "symbol": "VCB",
            "exchange": "HOSE",
            "trade_date": trade_date_str,
            "open": close - 200,
            "high": close + 300,
            "low": close - 400,
            "close": close,
            "volume": 1_500_000,
            "currency": "VND",
        },
    )


def test_list_dataset_for_instrument_filters_and_orders_by_trade_date() -> (
    None
):
    store = InMemoryTimeSeriesStore()
    older = _vn_daily_payload_record(
        "vn_stock:VCB", "2026-06-20", close=58000
    )
    newer = _vn_daily_payload_record(
        "vn_stock:VCB", "2026-06-24", close=58300
    )
    other = _vn_daily_payload_record(
        "vn_stock:VPB", "2026-06-24", close=21400
    )
    for record in (newer, older, other):
        store.records[(record.dataset_id, record.record_key)] = record

    rows = store.list_dataset_for_instrument(
        "vn_prices_daily", "vn_stock:VCB"
    )

    assert [row.payload["trade_date"] for row in rows] == [
        "2026-06-20",
        "2026-06-24",
    ]
    assert all(row.instrument_id == "vn_stock:VCB" for row in rows)


def test_list_dataset_for_instrument_unknown_dataset_returns_empty() -> (
    None
):
    store = InMemoryTimeSeriesStore()
    assert (
        store.list_dataset_for_instrument(
            "fictional_dataset", "vn_stock:VCB"
        )
        == []
    )


def test_read_instrument_returns_metadata_when_seeded() -> None:
    store = InMemoryTimeSeriesStore()
    store.instruments.append(_vcb_metadata())

    metadata = store.read_instrument("vn_stock:VCB")

    assert metadata is not None
    assert metadata.symbol == "VCB"
    assert metadata.display_name == "Vietcombank"
    assert store.read_instrument("vn_stock:NOPE") is None


def _seed_vcb_canonical(
    client: TestClient,
    *,
    trade_dates: tuple[str, ...] = ("2026-06-23", "2026-06-24"),
) -> None:
    store = client.app.state.platform.ingestion_service.store
    assert isinstance(store, InMemoryTimeSeriesStore)
    store.collection_memberships.add(("VN100", "vn_stock:VCB"))
    store.instruments.append(_vcb_metadata())
    for index, trade_date in enumerate(trade_dates):
        record = _vn_daily_payload_record(
            "vn_stock:VCB",
            trade_date,
            close=58000 + (index * 100),
        )
        store.records[(record.dataset_id, record.record_key)] = record


def test_vn_1d_chart_returns_canonical_rows_when_present(
    client: TestClient,
) -> None:
    _seed_vcb_canonical(client)

    response = client.get(
        "/api/market/instruments/vn_stock:VCB/chart?timeframe=1d"
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["timeframe"] == "1d"
    assert chart["instrument"]["symbol"] == "VCB"
    assert [record["time"] for record in chart["records"]] == [
        "2026-06-23",
        "2026-06-24",
    ]
    assert chart["records"][-1]["close"] == 58100
    assert chart["freshness"]["as_of"] == "2026-06-24"
    assert chart["freshness"]["status"] in {"fresh", "stale"}
    assert chart["lazy_fetch"]["status"] == "already_present"


def test_vn_1d_chart_falls_back_to_demo_when_no_canonical_rows(
    client: TestClient,
) -> None:
    store = client.app.state.platform.ingestion_service.store
    assert isinstance(store, InMemoryTimeSeriesStore)
    store.collection_memberships.add(("VN100", "vn_stock:VCB"))

    response = client.get(
        "/api/market/instruments/vn_stock:VCB/chart?timeframe=1d"
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["timeframe"] == "1d"
    assert chart["records"][0]["time"].startswith("2026-06-18T")
    assert "lazy_fetch" in chart


def test_vn_1d_chart_out_of_scope_short_circuits_with_empty_records(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/market/instruments/vn_stock:UNKNOWN/chart?timeframe=1d"
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["records"] == []
    assert chart["table"] == []
    assert chart["lazy_fetch"]["status"] == "out_of_scope"


def test_non_1d_vn_chart_uses_demo_path(client: TestClient) -> None:
    _seed_vcb_canonical(client)

    response = client.get(
        "/api/market/instruments/vn_stock:VCB/chart?timeframe=4h"
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["records"][0]["time"] == "2026-06-18T02:00:00+00:00"
    assert "lazy_fetch" not in chart


def test_non_vn_instrument_chart_uses_demo_path(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/market/instruments/us_stock:AAPL/chart?timeframe=1d"
    )

    assert response.status_code == 200
    chart = response.json()
    assert chart["instrument"]["symbol"] == "AAPL"
    assert "lazy_fetch" not in chart


def test_postgres_list_dataset_for_instrument_emits_filtered_select() -> (
    None
):
    class RowCursor(RecordingCursor):
        def fetchall(self) -> list[dict[str, Any]]:
            return [
                {
                    "market": "VN_STOCK",
                    "instrument_id": "vn_stock:VCB",
                    "symbol": "VCB",
                    "exchange": "HOSE",
                    "trade_date": datetime(2026, 6, 24).date(),
                    "open": 58000,
                    "high": 58400,
                    "low": 57800,
                    "close": 58200,
                    "volume": 1500000,
                    "value": None,
                    "currency": "VND",
                    "adjusted_close": None,
                    "corporate_action_flag": None,
                    "collected_at": datetime(2026, 6, 24, tzinfo=UTC),
                    "source_id": "vnstock",
                    "freshness_status": "fresh",
                }
            ]

    class RowConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.cursor_instance = RowCursor()

    connection = RowConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )

    rows = store.list_dataset_for_instrument(
        "vn_prices_daily", "vn_stock:VCB"
    )

    assert len(rows) == 1
    assert rows[0].instrument_id == "vn_stock:VCB"
    assert rows[0].payload["trade_date"] == "2026-06-24"
    last_sql, params = connection.cursor_instance.statements[-1]
    assert "FROM vn_prices_daily" in last_sql
    assert (
        "WHERE instrument_id = %(instrument_id)s" in last_sql
    )
    assert "ORDER BY trade_date ASC" in last_sql
    assert params == {"instrument_id": "vn_stock:VCB"}


def test_postgres_read_instrument_returns_metadata_when_row_exists() -> (
    None
):
    class InstrumentCursor(RecordingCursor):
        def fetchall(self) -> list[dict[str, Any]]:
            return [
                {
                    "instrument_id": "vn_stock:VCB",
                    "symbol": "VCB",
                    "market": "VN_STOCK",
                    "asset_class": "stock",
                    "exchange": "HOSE",
                    "display_name": "Vietcombank",
                    "currency": "VND",
                    "sector": "Financials",
                    "industry": "Banking",
                    "sub_industry": "Commercial Banking",
                    "status": "active",
                }
            ]

    class InstrumentConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.cursor_instance = InstrumentCursor()

    connection = InstrumentConnection()
    store = PostgresTimeSeriesStore(
        connection_factory=lambda: connection
    )

    metadata = store.read_instrument("vn_stock:VCB")

    assert metadata is not None
    assert metadata.symbol == "VCB"
    assert metadata.market == "VN_STOCK"
    last_sql, params = connection.cursor_instance.statements[-1]
    assert "FROM market_instruments" in last_sql
    assert params == {"instrument_id": "vn_stock:VCB"}


# ---------------------------------------------------------------------------
# T045 — VN-only freshness output with dataset-specific thresholds
# ---------------------------------------------------------------------------


from zoneinfo import ZoneInfo

from api.platform.freshness import (
    DATASET_RULES,
    DatasetFreshnessRule,
    FreshnessKind,
    active_freshness_dataset_ids,
    calculate_dataset_freshness,
)
from api.platform.ingestion.store_writer import IngestionJobRecord

_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _vn_daily_record(
    instrument_id: str,
    trade_date: datetime,
) -> TimeSeriesRecord:
    return TimeSeriesRecord(
        dataset_id="vn_prices_daily",
        record_key=f"{instrument_id}:{trade_date.date().isoformat()}",
        instrument_id=instrument_id,
        market_time=trade_date,
        collected_at=trade_date,
        source_id="vn_prices_daily",
        payload={
            "symbol": "VCB",
            "exchange": "HOSE",
            "trade_date": trade_date.date().isoformat(),
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 1000,
            "currency": "VND",
        },
    )


def _vn_hourly_record(
    instrument_id: str,
    interval_start: datetime,
) -> TimeSeriesRecord:
    return TimeSeriesRecord(
        dataset_id="vn_prices",
        record_key=f"{instrument_id}:{interval_start.isoformat()}",
        instrument_id=instrument_id,
        market_time=interval_start,
        collected_at=interval_start,
        source_id="vn_prices",
        payload={
            "symbol": "VCB",
            "exchange": "HOSE",
            "interval_start": interval_start.isoformat(),
            "interval_end": (
                interval_start + timedelta(hours=1)
            ).isoformat(),
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 1000,
            "currency": "VND",
        },
    )


def test_active_freshness_dataset_ids_vn_only_by_default() -> None:
    assert active_freshness_dataset_ids(False) == [
        "vn_prices_daily",
        "vn_prices",
    ]


def test_active_freshness_dataset_ids_roadmap_restores_full_list() -> None:
    assert active_freshness_dataset_ids(True) == [
        "vn_prices_daily",
        "vn_prices",
        "us_prices",
        "us_prices_daily",
        "xauusd_prices",
        "xauusd_prices_daily",
        "sjc_gold_prices",
    ]


def test_dataset_rules_expose_vn_daily_and_hourly_thresholds() -> None:
    assert DATASET_RULES["vn_prices_daily"] == DatasetFreshnessRule(
        dataset_id="vn_prices_daily",
        kind=FreshnessKind.DAILY,
        max_lag=timedelta(days=1),
    )
    assert DATASET_RULES["vn_prices"] == DatasetFreshnessRule(
        dataset_id="vn_prices",
        kind=FreshnessKind.HOURLY,
        max_lag=timedelta(hours=6),
    )


def test_inmemory_store_freshness_is_vn_only_by_default() -> None:
    store = InMemoryTimeSeriesStore()

    entries = store.freshness()

    assert [entry["dataset"] for entry in entries] == [
        "vn_prices_daily",
        "vn_prices",
    ]


def test_inmemory_store_freshness_roadmap_restores_full_list() -> None:
    store = InMemoryTimeSeriesStore(roadmap_markets_enabled=True)

    entries = store.freshness()

    assert [entry["dataset"] for entry in entries] == [
        "vn_prices_daily",
        "vn_prices",
        "us_prices",
        "us_prices_daily",
        "xauusd_prices",
        "xauusd_prices_daily",
        "sjc_gold_prices",
    ]


def test_vn_prices_daily_fresh_when_trade_date_is_today_vn() -> None:
    now_vn = datetime(2026, 6, 24, 15, 0, tzinfo=_VN_TZ)
    today_record = _vn_daily_record(
        "vn_stock:VCB",
        datetime(2026, 6, 24, tzinfo=UTC),
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices_daily"],
        list_dataset=lambda _id: [today_record],
        list_jobs=lambda: [],
        now=now_vn,
    )

    assert entries[0]["status"] == "fresh"


def test_vn_prices_daily_stale_when_three_weekdays_old() -> None:
    # Thursday 2026-06-25; latest trade_date Monday 2026-06-22 → 3 days old
    now_vn = datetime(2026, 6, 25, 10, 0, tzinfo=_VN_TZ)
    stale_record = _vn_daily_record(
        "vn_stock:VCB",
        datetime(2026, 6, 22, tzinfo=UTC),
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices_daily"],
        list_dataset=lambda _id: [stale_record],
        list_jobs=lambda: [],
        now=now_vn,
    )

    assert entries[0]["status"] == "stale"


def test_vn_prices_daily_monday_tolerates_weekend() -> None:
    # Monday 2026-06-22; latest trade_date Friday 2026-06-19 → 3 days
    now_vn = datetime(2026, 6, 22, 9, 30, tzinfo=_VN_TZ)
    friday_record = _vn_daily_record(
        "vn_stock:VCB",
        datetime(2026, 6, 19, tzinfo=UTC),
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices_daily"],
        list_dataset=lambda _id: [friday_record],
        list_jobs=lambda: [],
        now=now_vn,
    )

    assert entries[0]["status"] == "fresh"


def test_vn_prices_daily_missing_when_no_records() -> None:
    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices_daily"],
        list_dataset=lambda _id: [],
        list_jobs=lambda: [],
        now=datetime(2026, 6, 25, 10, 0, tzinfo=_VN_TZ),
    )

    assert entries[0]["status"] == "missing"
    assert entries[0]["as_of"] is None


def test_vn_prices_daily_failed_overrides_record_presence() -> None:
    now_vn = datetime(2026, 6, 25, 10, 0, tzinfo=_VN_TZ)
    record = _vn_daily_record(
        "vn_stock:VCB",
        datetime(2026, 6, 25, tzinfo=UTC),
    )
    failed_job = IngestionJobRecord(
        job_id="ingest_0001",
        source_id="vn_prices_daily",
        dataset_id="vn_prices_daily",
        period="2026-06-25",
        trigger="manual",
        status="failed",
        started_at=now_vn,
        completed_at=now_vn,
        record_count=0,
        diagnostics={"error": "boom"},
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices_daily"],
        list_dataset=lambda _id: [record],
        list_jobs=lambda: [failed_job],
        now=now_vn,
    )

    assert entries[0]["status"] == "failed"


def test_vn_prices_hourly_fresh_within_six_hours() -> None:
    now_vn = datetime(2026, 6, 24, 15, 0, tzinfo=_VN_TZ)
    recent = _vn_hourly_record(
        "vn_stock:VCB",
        now_vn - timedelta(hours=2),
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices"],
        list_dataset=lambda _id: [recent],
        list_jobs=lambda: [],
        now=now_vn,
    )

    assert entries[0]["status"] == "fresh"


def test_vn_prices_hourly_stale_after_six_hours() -> None:
    now_vn = datetime(2026, 6, 24, 15, 0, tzinfo=_VN_TZ)
    stale = _vn_hourly_record(
        "vn_stock:VCB",
        now_vn - timedelta(hours=8),
    )

    entries = calculate_dataset_freshness(
        dataset_ids=["vn_prices"],
        list_dataset=lambda _id: [stale],
        list_jobs=lambda: [],
        now=now_vn,
    )

    assert entries[0]["status"] == "stale"
