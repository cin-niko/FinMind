from finmind_agents.dataflows.models import (
    DataflowProviderResult,
    DataflowCollectionRequest,
    DatasetGroup,
    CollectionStatus,
)
from finmind_agents.dataflows.providers.base import ProviderCapability, ProviderFetchResult
from finmind_agents.models import Market


class AlphaVantageProvider:
    provider_id = "alpha_vantage"
    capabilities = (
        ProviderCapability(
            market=Market.US_STOCK,
            dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.NEWS),
        ),
    )

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        if not self._api_key:
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=_supported_groups(request.dataset_groups),
                    status=CollectionStatus.SKIPPED,
                    warnings=("alpha_vantage_api_key_missing",),
                    failure_reason="Alpha Vantage API key is not configured",
                )
            )
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id,
                dataset_groups=_supported_groups(request.dataset_groups),
                status=CollectionStatus.SKIPPED,
                warnings=("alpha_vantage_live_fetch_not_enabled",),
                failure_reason="Alpha Vantage live collection is not enabled in this harness",
            )
        )


def _supported_groups(groups: tuple[DatasetGroup, ...]) -> tuple[DatasetGroup, ...]:
    return tuple(
        group
        for group in groups
        if group in {DatasetGroup.MARKET_PRICE, DatasetGroup.NEWS}
    )
