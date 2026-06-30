from datetime import UTC, datetime

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    ExecutionRun,
    Market,
    SourceDocument,
)
from finmind_agents.repositories import MarketDataRepository, RunRepository
from finmind_agents.workflows.catalog import build_workflow_catalog
from finmind_agents.workflows.specs import WorkflowCatalog


class InMemoryMarketDataRepository(MarketDataRepository):
    def __init__(self) -> None:
        collected_at = datetime(2026, 6, 18, 8, 0, tzinfo=UTC)
        self._records = [
            CanonicalMarketDataRecord(
                dataset_id="vn_prices",
                record_key="VNINDEX-prices",
                instrument_id="VNINDEX",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_prices",
                payload={
                    "series": [
                        {"date": "2026-06-18", "open": None, "high": None, "low": None,
                         "close": 1285.4, "change_percent": 0.82, "volume": 812000000},
                    ],
                    "count": 1,
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-18",
                    "interval": "1D",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="vn_prices",
                record_key="VCB-prices",
                instrument_id="VCB",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_prices",
                payload={
                    "series": [
                        {"date": "2026-06-18", "open": None, "high": None, "low": None,
                         "close": 58200, "change_percent": 1.14, "volume": 4920000},
                    ],
                    "count": 1,
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-18",
                    "interval": "1D",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="us_prices",
                record_key="AAPL-prices",
                instrument_id="AAPL",
                market_time=datetime(2026, 6, 18, 20, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_us_prices",
                payload={
                    "series": [
                        {"date": "2026-06-18", "open": None, "high": None, "low": None,
                         "close": 195.64, "change_percent": 0.42, "volume": 52100000},
                    ],
                    "count": 1,
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-18",
                    "interval": "1D",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="vn_fundamentals",
                record_key="VCB-FY2025",
                instrument_id="VCB",
                market_time=datetime(2026, 3, 31, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_fundamentals",
                payload={
                    "eps": 5200,
                    "bvps": 35600,
                    "roe_percent": 20.3,
                    "period": "FY2025",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="us_fundamentals",
                record_key="AAPL-FY2025",
                instrument_id="AAPL",
                market_time=datetime(2026, 3, 31, 20, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_us_fundamentals",
                payload={
                    "eps": 7.42,
                    "revenue_growth_percent": 5.6,
                    "roe_percent": 48.1,
                    "period": "FY2025",
                },
            ),
        ]
        self._source_documents = [
            SourceDocument(
                document_id="doc_vcb_demo",
                source_id="demo_curated_sources",
                title="VCB curated company update",
                published_at=datetime(2026, 6, 18, 6, 30, tzinfo=UTC),
                collected_at=collected_at,
                url_or_reference="demo://vn/vcb/update",
                content_excerpt="Curated demo update for VCB banking fundamentals.",
                market_scope=Market.VN_STOCK,
                instrument_ids=("VCB",),
                sentiment_hint="neutral",
            ),
        ]

    def list_by_market(
        self,
        market: Market,
    ) -> list[CanonicalMarketDataRecord]:
        dataset_prefix_by_market = {
            Market.VN_STOCK: "vn_",
            Market.US_STOCK: "us_",
        }
        dataset_prefix = dataset_prefix_by_market[market]
        return [
            record
            for record in self._records
            if record.dataset_id.startswith(dataset_prefix)
        ]

    def list_source_documents(
        self,
        market: Market,
        symbol: str | None,
    ) -> list[SourceDocument]:
        return [
            document
            for document in self._source_documents
            if document.market_scope == market
            and (symbol is None or symbol in document.instrument_ids)
        ]


class InMemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._runs: dict[str, ExecutionRun] = {}

    def save(self, run: ExecutionRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> ExecutionRun | None:
        return self._runs.get(run_id)

    def list(self) -> list[ExecutionRun]:
        return sorted(
            self._runs.values(),
            key=lambda run: run.started_at,
            reverse=True,
        )

    def delete(self, run_id: str) -> bool:
        existed = run_id in self._runs
        self._runs.pop(run_id, None)
        return existed

    def update_title(self, run_id: str, title: str) -> ExecutionRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        from dataclasses import replace

        updated = replace(run, title=title)
        self._runs[run_id] = updated
        return updated


def create_workflow_catalog() -> WorkflowCatalog:
    return WorkflowCatalog(build_workflow_catalog())
