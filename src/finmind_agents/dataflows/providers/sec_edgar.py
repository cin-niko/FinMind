from finmind_agents.dataflows.models import (
    DataflowProviderResult,
    DataflowCollectionRequest,
    DatasetGroup,
    CollectionStatus,
)
from finmind_agents.dataflows.providers.base import ProviderCapability, ProviderFetchResult
from finmind_agents.models import Market


class SecEdgarProvider:
    provider_id = "sec_edgar"
    capabilities = (
        ProviderCapability(
            market=Market.US_STOCK,
            dataset_groups=(DatasetGroup.FUNDAMENTAL,),
        ),
    )

    def __init__(self, user_agent: str = "") -> None:
        self._user_agent = user_agent

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        if not self._user_agent:
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=_supported_groups(request.dataset_groups),
                    status=CollectionStatus.SKIPPED,
                    warnings=("sec_edgar_user_agent_missing",),
                    failure_reason="SEC EDGAR User-Agent is not configured",
                )
            )
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id,
                dataset_groups=_supported_groups(request.dataset_groups),
                status=CollectionStatus.SKIPPED,
                warnings=("sec_edgar_live_fetch_not_enabled",),
                failure_reason="SEC EDGAR live collection is not enabled in this harness",
            )
        )


def _supported_groups(groups: tuple[DatasetGroup, ...]) -> tuple[DatasetGroup, ...]:
    return tuple(group for group in groups if group == DatasetGroup.FUNDAMENTAL)
