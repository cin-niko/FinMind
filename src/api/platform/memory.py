from datetime import UTC, datetime

from api.platform.models import CanonicalMarketDataRecord, ExecutionRun, FreshnessStatus, Market
from api.platform.repositories import MarketDataRepository, RunRepository
from api.platform.workflows.catalog import build_workflow_catalog
from api.platform.workflows.specs import WorkflowCatalog


class InMemoryMarketDataRepository(MarketDataRepository):
    def __init__(self) -> None:
        collected_at = datetime(2026, 6, 18, 8, 0, tzinfo=UTC)
        self._records = [
            CanonicalMarketDataRecord(
                dataset_id="vn_prices",
                record_key="VNINDEX-2026-06-18",
                instrument_id="VNINDEX",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_prices",
                payload={"close": 1285.4, "change_percent": 0.82, "volume": 812000000},
                freshness_status=FreshnessStatus.FRESH,
            ),
            CanonicalMarketDataRecord(
                dataset_id="gold_spot",
                record_key="SJC-2026-06-18",
                instrument_id="SJC",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_gold_spot",
                payload={"close": 76400000, "change_percent": -0.18, "unit": "VND/tael"},
                freshness_status=FreshnessStatus.FRESH,
            ),
        ]

    def list_by_market(self, market: Market) -> list[CanonicalMarketDataRecord]:
        dataset_by_market = {
            Market.VN_STOCK: "vn_prices",
            Market.GOLD: "gold_spot",
        }
        dataset_id = dataset_by_market[market]
        return [record for record in self._records if record.dataset_id == dataset_id]


class InMemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._runs: dict[str, ExecutionRun] = {}

    def save(self, run: ExecutionRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> ExecutionRun | None:
        return self._runs.get(run_id)


def create_workflow_catalog() -> WorkflowCatalog:
    return WorkflowCatalog(build_workflow_catalog())
