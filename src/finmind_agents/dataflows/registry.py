from collections.abc import Iterable
from dataclasses import dataclass

from finmind_agents.dataflows.models import DatasetGroup
from finmind_agents.dataflows.providers.base import DataflowProvider
from finmind_agents.dataflows.providers.vnstock import VnstockProvider
from finmind_agents.models import Market


@dataclass(frozen=True)
class DataflowProviderRegistry:
    providers: tuple[DataflowProvider, ...]

    def providers_for(
        self,
        market: Market,
        dataset_groups: tuple[DatasetGroup, ...],
    ) -> tuple[DataflowProvider, ...]:
        requested = set(dataset_groups)
        return tuple(
            provider
            for provider in self.providers
            if any(
                capability.market == market
                and requested.intersection(capability.dataset_groups)
                for capability in provider.capabilities
            )
        )


def build_default_provider_registry(
    *,
    vn_data_provider: str = "vnstock",
    vnstock_api_key: str = "",
    extra_providers: Iterable[DataflowProvider] = (),
) -> DataflowProviderRegistry:
    vn_providers: tuple[DataflowProvider, ...]
    if vn_data_provider == "vnstock":
        vn_providers = (VnstockProvider(api_key=vnstock_api_key),)
    else:
        vn_providers = ()
    return DataflowProviderRegistry(
        providers=(
            *vn_providers,
            *tuple(extra_providers),
        )
    )
