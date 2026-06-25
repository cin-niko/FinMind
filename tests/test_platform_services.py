from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.platform.ingestion.demo_sources import DemoMarketDataSource
import api.platform.ingestion.free_sources as free_sources
from api.platform.ingestion.backfill import (
    run_historical_backfill,
    run_market_history_backfill,
    run_market_latest_fetch,
    run_us_daily_history_backfill,
    run_us_xauusd_history_backfill,
)
from api.platform.ingestion.free_sources import (
    AlphaVantageXauusdDailySource,
    SJCOfficialGoldSource,
    StooqUSStockDailySource,
    YFinanceUSStockSource,
    VnstockVNStockSource,
    YFinanceXauusdSource,
    create_real_sources,
    _alpha_vantage_xauusd_daily_fetcher,
    _stooq_us_stock_daily_fetcher,
)
from api.platform.ingestion.service import IngestionService
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
    assert freshness["vn_prices"]["status"] == "fresh"
    assert freshness["vn_prices"]["record_count"] == 6

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

    def fetch(self, period: str) -> list[TimeSeriesRecord]:
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

        def fetch(self, period: str) -> list[TimeSeriesRecord]:
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

        def fetch(self, period: str) -> list[TimeSeriesRecord]:
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

        def fetch(self, period: str) -> list[TimeSeriesRecord]:
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

        def fetch(self, _period: str) -> list[TimeSeriesRecord]:
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
    store = InMemoryTimeSeriesStore()
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
    store = InMemoryTimeSeriesStore()
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
