from finmind_agents.dataflows.models import (
    DataflowProviderResult,
    DataflowCollectionRequest,
    DatasetGroup,
    CollectionStatus,
)
from finmind_agents.dataflows.providers.base import (
    ProviderCapability,
    ProviderFetchResult,
)
from finmind_agents.models import Market
from finmind_agents.repositories import MarketDataRepository


class OfflineFallbackProvider:
    provider_id = "offline_fallback"
    capabilities = (
        ProviderCapability(
            market=Market.VN_STOCK,
            dataset_groups=(
                DatasetGroup.MARKET_PRICE,
                DatasetGroup.FUNDAMENTAL,
                DatasetGroup.NEWS,
            ),
        ),
        ProviderCapability(
            market=Market.US_STOCK,
            dataset_groups=(
                DatasetGroup.MARKET_PRICE,
                DatasetGroup.FUNDAMENTAL,
                DatasetGroup.NEWS,
            ),
        ),
    )

    def __init__(self, market_data: MarketDataRepository) -> None:
        self._market_data = market_data

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        records = [
            record
            for record in self._market_data.list_by_market(request.market)
            if _record_matches_groups(record.dataset_id, request.dataset_groups)
            and record.instrument_id == request.symbol
        ]
        source_documents = ()
        if DatasetGroup.NEWS in request.dataset_groups:
            source_documents = tuple(
                self._market_data.list_source_documents(request.market, request.symbol)
            )
        warnings: list[str] = []
        if DatasetGroup.NEWS in request.dataset_groups and not source_documents:
            warnings.append("news_fallback_unavailable")
        if (
            DatasetGroup.MARKET_PRICE in request.dataset_groups
            and not any(record.dataset_id.endswith("_prices") for record in records)
        ):
            warnings.append("market_price_fallback_unavailable")
        if (
            DatasetGroup.FUNDAMENTAL in request.dataset_groups
            and not any(record.dataset_id.endswith("_fundamentals") for record in records)
        ):
            warnings.append("fundamental_fallback_unavailable")
        status = (
            CollectionStatus.FALLBACK
            if records or source_documents
            else CollectionStatus.FAILED
        )
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id,
                dataset_groups=request.dataset_groups,
                status=status,
                source_ids=tuple(sorted({record.source_id for record in records})),
                warnings=tuple(warnings),
                failure_reason="offline fallback has no matching data"
                if status == CollectionStatus.FAILED
                else None,
            ),
            records=tuple(records),
            source_documents=source_documents,
        )


def _record_matches_groups(
    dataset_id: str,
    dataset_groups: tuple[DatasetGroup, ...],
) -> bool:
    return (
        DatasetGroup.MARKET_PRICE in dataset_groups
        and dataset_id.endswith("_prices")
        or DatasetGroup.FUNDAMENTAL in dataset_groups
        and dataset_id.endswith("_fundamentals")
    )
