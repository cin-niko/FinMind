from dataclasses import dataclass

from api.settings import Settings
from api.platform.memory import (
    InMemoryMarketDataRepository,
    InMemoryRunRepository,
    create_workflow_catalog,
)
from api.platform.ingestion.demo_sources import DemoMarketDataSource, create_demo_sources
from api.platform.ingestion.free_sources import (
    AlphaVantageXauusdDailySource,
    SJCOfficialGoldSource,
    StooqUSStockDailySource,
    YFinanceUSStockSource,
    VnstockVNStockSource,
    YFinanceXauusdSource,
)
from api.platform.ingestion.service import IngestionService
from api.platform.ingestion.store_writer import InMemoryTimeSeriesStore, TimeSeriesStore
from api.platform.market import MarketService, create_demo_market_service
from api.platform.storage.postgres import PostgresTimeSeriesStore
from api.platform.workflows.service import WorkflowService


@dataclass(frozen=True)
class Platform:
    workflow_service: WorkflowService
    market_service: MarketService
    ingestion_service: IngestionService


def create_demo_platform(settings: Settings | None = None) -> Platform:
    runs = InMemoryRunRepository()
    return Platform(
        workflow_service=WorkflowService(
            workflows=create_workflow_catalog(),
            market_data=InMemoryMarketDataRepository(),
            runs=runs,
        ),
        market_service=create_demo_market_service(),
        ingestion_service=create_ingestion_service(settings),
    )


def create_ingestion_service(settings: Settings | None = None) -> IngestionService:
    return IngestionService(
        sources=_create_ingestion_sources(settings),
        store=_create_ingestion_store(settings),
    )


def _create_ingestion_store(settings: Settings | None) -> TimeSeriesStore:
    if settings is not None and settings.database_url:
        return PostgresTimeSeriesStore(database_url=settings.database_url)
    return InMemoryTimeSeriesStore()


def _create_ingestion_sources(settings: Settings | None):
    if settings is None:
        return create_demo_sources()

    sources = {}
    if settings.vn_provider == "mock":
        sources["vn_prices"] = DemoMarketDataSource("vn_prices")
    else:
        sources["vn_prices"] = VnstockVNStockSource(
            api_key=settings.vnstock_api_key,
            timeout_seconds=settings.provider_timeout_seconds,
        )

    if settings.us_provider == "mock":
        sources["us_prices"] = DemoMarketDataSource("us_prices")
        sources["us_prices_daily"] = DemoMarketDataSource("us_prices_daily")
    else:
        sources["us_prices"] = YFinanceUSStockSource(
            timeout_seconds=settings.provider_timeout_seconds,
        )
        sources["us_prices_daily"] = StooqUSStockDailySource(
            timeout_seconds=settings.provider_timeout_seconds,
        )

    if settings.xauusd_provider == "mock":
        sources["xauusd_prices"] = DemoMarketDataSource("xauusd_prices")
    else:
        sources["xauusd_prices"] = YFinanceXauusdSource(
            timeout_seconds=settings.provider_timeout_seconds,
        )
        if settings.xauusd_daily_fallback == "alpha_vantage":
            sources["xauusd_prices_daily"] = AlphaVantageXauusdDailySource(
                api_key=settings.alpha_vantage_api_key,
                timeout_seconds=settings.provider_timeout_seconds,
            )

    if settings.sjc_provider == "mock":
        sources["sjc_gold_prices"] = DemoMarketDataSource("sjc_gold_prices")
    else:
        sources["sjc_gold_prices"] = SJCOfficialGoldSource(
            timeout_seconds=settings.provider_timeout_seconds,
        )
    return sources
