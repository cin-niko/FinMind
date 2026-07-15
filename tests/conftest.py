from __future__ import annotations

from collections.abc import Iterator

import pytest

from finmind_agents.dataflows.models import (
    CollectionStatus,
    DataflowCollectionRequest,
    DataflowProviderResult,
    DatasetGroup,
)
from finmind_agents.dataflows.providers.base import (
    ProviderCapability,
    ProviderFetchResult,
)
from finmind_agents.memory import InMemoryMarketDataRepository
from finmind_agents.models import CanonicalMarketDataRecord, Market, SourceDocument


class _FixtureMarketDataProvider:
    """Deterministic market provider used only by API and workflow tests."""

    provider_id = "test_market_data"

    def __init__(self) -> None:
        self._market_data = InMemoryMarketDataRepository()
        self.capabilities = (
            ProviderCapability(
                market=Market.VN_STOCK,
                dataset_groups=(
                    DatasetGroup.MARKET_PRICE,
                    DatasetGroup.FUNDAMENTAL,
                    DatasetGroup.COMPANY_PROFILE,
                    DatasetGroup.NEWS,
                ),
            ),
        )

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        records = tuple(
            record
            for record in self._market_data.list_by_market(request.market)
            if record.instrument_id == request.symbol
            and _matches_requested_group(record.dataset_id, request.dataset_groups)
        )
        source_documents = (
            tuple(self._market_data.list_source_documents(request.market, request.symbol))
            if DatasetGroup.NEWS in request.dataset_groups
            else ()
        )
        warnings = tuple(
            f"{group.value}_unavailable"
            for group in request.dataset_groups
            if not _group_has_data(group, records, source_documents)
        )
        has_data = bool(records or source_documents)
        status = CollectionStatus.FAILED if not has_data else CollectionStatus.PARTIAL if warnings else CollectionStatus.SUCCESS
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id, dataset_groups=request.dataset_groups, status=status,
                source_ids=tuple(sorted({record.source_id for record in records})), warnings=warnings,
                failure_reason="test provider has no matching data" if status == CollectionStatus.FAILED else None,
            ), records=records, source_documents=source_documents,
        )


class _FixtureGoldProvider:
    provider_id = "test_gold"

    def __init__(self) -> None:
        self.capabilities = (
            ProviderCapability(market=Market.GOLD, dataset_groups=(DatasetGroup.MARKET_PRICE,)),
        )

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        from datetime import UTC, datetime

        if request.symbol != "XAUUSD":
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id, dataset_groups=request.dataset_groups,
                    status=CollectionStatus.FAILED, failure_reason="unsupported_gold_instrument",
                )
            )
        record = CanonicalMarketDataRecord(
            dataset_id="gold_prices", record_key="XAUUSD-prices", instrument_id="XAUUSD",
            market_time=datetime(2026, 6, 18, tzinfo=UTC), collected_at=datetime(2026, 6, 18, 8, tzinfo=UTC),
            source_id=self.provider_id,
            payload={"series": [{"date": "2026-06-17", "open": 2320.0, "high": 2340.0, "low": 2315.0, "close": 2330.0, "volume": None}, {"date": "2026-06-18", "open": 2330.0, "high": 2350.0, "low": 2325.0, "close": 2345.0, "volume": None}], "count": 2, "start_date": "2026-06-17", "end_date": "2026-06-18", "interval": "1D"},
        )
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(provider_id=self.provider_id, dataset_groups=request.dataset_groups, status=CollectionStatus.SUCCESS, source_ids=(self.provider_id,)), records=(record,)
        )

def _matches_requested_group(dataset_id: str, groups: tuple[DatasetGroup, ...]) -> bool:
    return (
        (DatasetGroup.MARKET_PRICE in groups and dataset_id.endswith("_prices"))
        or (DatasetGroup.FUNDAMENTAL in groups and dataset_id.endswith("_fundamentals"))
        or (
            DatasetGroup.COMPANY_PROFILE in groups
            and dataset_id.endswith("_company_profile")
        )
    )


def _group_has_data(
    group: DatasetGroup,
    records: tuple[CanonicalMarketDataRecord, ...],
    source_documents: tuple[SourceDocument, ...],
) -> bool:
    if group == DatasetGroup.MARKET_PRICE:
        return any(record.dataset_id.endswith("_prices") for record in records)
    if group == DatasetGroup.FUNDAMENTAL:
        return any(
            record.dataset_id.endswith("_fundamentals")
            for record in records
        )
    if group == DatasetGroup.COMPANY_PROFILE:
        return any(
            record.dataset_id.endswith("_company_profile")
            for record in records
        )
    if group == DatasetGroup.NEWS:
        return bool(source_documents)
    return False


@pytest.fixture(autouse=True)
def _in_memory_conversation_store(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Inject a fresh in-memory run repository for every test.

    The product run store is PostgreSQL; tests override the ``build_run_store``
    seam so the suite stays self-contained, fast, and offline. Each test gets a
    fresh repository so run state never leaks between tests.
    """
    from finmind_agents.memory import InMemoryConversationRepository

    repo = InMemoryConversationRepository()
    monkeypatch.setattr(
        "finmind_api.platform.build_conversation_store",
        lambda settings: repo,
    )
    yield


@pytest.fixture(autouse=True)
def _fixture_dataflow_provider(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep tests deterministic without enabling production data substitution."""
    from finmind_agents.dataflows.registry import DataflowProviderRegistry

    registry = DataflowProviderRegistry(providers=(_FixtureMarketDataProvider(), _FixtureGoldProvider()))
    monkeypatch.setattr(
        "finmind_api.platform.build_default_provider_registry",
        lambda **_kwargs: registry,
    )
    yield
