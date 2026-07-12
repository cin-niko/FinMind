from dataclasses import dataclass
from dataclasses import replace
from uuid import uuid4

from finmind_agents.dataflows.models import (
    DataflowCollectionRequest,
    DataflowCollectionResult,
    CollectionStatus,
    dataflow_now,
)
from finmind_agents.dataflows.providers.base import ProviderFetchResult
from finmind_agents.dataflows.registry import DataflowProviderRegistry


@dataclass(frozen=True)
class DataflowService:
    registry: DataflowProviderRegistry

    def collect(self, request: DataflowCollectionRequest) -> DataflowCollectionResult:
        started_at = dataflow_now()
        dataset_groups = request.effective_dataset_groups()
        provider_request = replace(request, dataset_groups=dataset_groups)
        fetch_results: list[ProviderFetchResult] = []
        records = []
        source_documents = []
        providers = self.registry.providers_for(
            market=request.market,
            dataset_groups=dataset_groups,
        )
        for provider in providers:
            result = provider.fetch(provider_request)
            fetch_results.append(result)
            records.extend(result.records)
            source_documents.extend(result.source_documents)

        provider_results = tuple(result.provider_result for result in fetch_results)
        warnings = tuple(
            warning
            for provider in provider_results
            for warning in provider.warnings
        )
        failure_reasons = tuple(
            provider.failure_reason
            for provider in provider_results
            if provider.failure_reason
        )
        status = _result_status(
            provider_statuses=tuple(provider.status for provider in provider_results),
            has_data=bool(records or source_documents),
            warnings=warnings,
        )
        return DataflowCollectionResult(
            collection_id=f"collection_{uuid4().hex[:12]}",
            market=request.market,
            symbol=request.symbol,
            requested_dataset_groups=dataset_groups,
            provider_results=provider_results,
            records=tuple(records),
            source_documents=tuple(source_documents),
            status=status,
            warnings=warnings,
            failure_reasons=failure_reasons,
            started_at=started_at,
            completed_at=dataflow_now(),
        )


def _result_status(
    provider_statuses: tuple[CollectionStatus, ...],
    has_data: bool,
    warnings: tuple[str, ...],
) -> CollectionStatus:
    if not has_data:
        return CollectionStatus.FAILED
    if CollectionStatus.SUCCESS in provider_statuses and not warnings:
        return CollectionStatus.SUCCESS
    return CollectionStatus.PARTIAL

