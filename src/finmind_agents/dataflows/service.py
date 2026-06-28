from dataclasses import dataclass
from dataclasses import replace
from uuid import uuid4

from finmind_agents.dataflows.models import (
    DataflowRetrievalRequest,
    DataflowRetrievalResult,
    RetrievalStatus,
    dataflow_now,
)
from finmind_agents.dataflows.providers.base import ProviderFetchResult
from finmind_agents.dataflows.registry import DataflowProviderRegistry


@dataclass(frozen=True)
class DataflowService:
    registry: DataflowProviderRegistry

    def retrieve(self, request: DataflowRetrievalRequest) -> DataflowRetrievalResult:
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
        fallback_providers = [
            provider for provider in providers if provider.provider_id == "offline_fallback"
        ]
        live_providers = [
            provider for provider in providers if provider.provider_id != "offline_fallback"
        ]
        for provider in live_providers:
            result = provider.fetch(provider_request)
            fetch_results.append(result)
            records.extend(result.records)
            source_documents.extend(result.source_documents)

        missing_groups = _missing_groups(
            requested_groups=dataset_groups,
            records=tuple(records),
            source_document_count=len(source_documents),
        )
        if missing_groups and request.allow_fallback:
            fallback_request = replace(provider_request, dataset_groups=missing_groups)
            for provider in fallback_providers:
                result = provider.fetch(fallback_request)
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
        return DataflowRetrievalResult(
            retrieval_id=f"retrieval_{uuid4().hex[:12]}",
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
    provider_statuses: tuple[RetrievalStatus, ...],
    has_data: bool,
    warnings: tuple[str, ...],
) -> RetrievalStatus:
    if not has_data:
        return RetrievalStatus.FAILED
    if RetrievalStatus.SUCCESS in provider_statuses and not warnings:
        return RetrievalStatus.SUCCESS
    if RetrievalStatus.FALLBACK in provider_statuses and not warnings:
        return RetrievalStatus.FALLBACK
    return RetrievalStatus.PARTIAL


def _missing_groups(
    requested_groups: tuple,
    records: tuple,
    source_document_count: int,
) -> tuple:
    missing = []
    for group in requested_groups:
        if group.value == "market_price" and not any(
            record.dataset_id.endswith("_prices") for record in records
        ):
            missing.append(group)
        if group.value == "fundamental" and not any(
            record.dataset_id.endswith("_fundamentals") for record in records
        ):
            missing.append(group)
        if group.value == "news" and source_document_count == 0:
            missing.append(group)
    return tuple(missing)
