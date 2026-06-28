from dataclasses import dataclass
from typing import Protocol

from finmind_agents.dataflows.models import (
    DataflowProviderResult,
    DataflowRetrievalRequest,
    DatasetGroup,
)
from finmind_agents.models import CanonicalMarketDataRecord, Market, SourceDocument


@dataclass(frozen=True)
class ProviderCapability:
    market: Market
    dataset_groups: tuple[DatasetGroup, ...]


@dataclass(frozen=True)
class ProviderFetchResult:
    provider_result: DataflowProviderResult
    records: tuple[CanonicalMarketDataRecord, ...] = ()
    source_documents: tuple[SourceDocument, ...] = ()


class DataflowProvider(Protocol):
    provider_id: str
    capabilities: tuple[ProviderCapability, ...]

    def fetch(self, request: DataflowRetrievalRequest) -> ProviderFetchResult: ...
