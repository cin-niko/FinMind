from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from finmind_agents.models import CanonicalMarketDataRecord, Market, SourceDocument


class DatasetGroup(StrEnum):
    MARKET_PRICE = "market_price"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"


class CollectionStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    FALLBACK = "fallback"
    SKIPPED = "skipped"


class CollectionPlanStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    PARTIAL = "partial"


def dataflow_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class DataRequirement:
    dataset: str
    params: dict[str, object] = field(default_factory=dict)
    required: bool = True

    def dataset_group(self) -> DatasetGroup:
        mapping = {
            "ohlcv": DatasetGroup.MARKET_PRICE,
            "market_price": DatasetGroup.MARKET_PRICE,
            "price_history": DatasetGroup.MARKET_PRICE,
            "financial_statement": DatasetGroup.FUNDAMENTAL,
            "valuation_ratios": DatasetGroup.FUNDAMENTAL,
            "corporate_events": DatasetGroup.FUNDAMENTAL,
            "company_profile": DatasetGroup.FUNDAMENTAL,
            "fundamental": DatasetGroup.FUNDAMENTAL,
            "source_documents": DatasetGroup.NEWS,
            "news": DatasetGroup.NEWS,
        }
        try:
            return mapping[self.dataset]
        except KeyError as error:
            raise ValueError(f"Unsupported data requirement dataset: {self.dataset}") from error


@dataclass(frozen=True)
class AgentCollectionPlan:
    skill_id: str
    market: Market
    symbol: str
    required_requests: tuple[DataRequirement, ...]
    optional_requests: tuple[DataRequirement, ...] = ()
    policy_id: str = "workflow_strict"
    status: CollectionPlanStatus = CollectionPlanStatus.PROPOSED

    def all_requests(self) -> tuple[DataRequirement, ...]:
        return (*self.required_requests, *self.optional_requests)


@dataclass(frozen=True)
class DataflowCollectionRequest:
    market: Market
    symbol: str
    requested_by: str
    dataset_groups: tuple[DatasetGroup, ...] = ()
    data_requirements: tuple[DataRequirement, ...] = ()
    lookback: str | None = None
    allow_fallback: bool = True

    def effective_dataset_groups(self) -> tuple[DatasetGroup, ...]:
        groups: list[DatasetGroup] = []
        for group in self.dataset_groups:
            if group not in groups:
                groups.append(group)
        for requirement in self.data_requirements:
            group = requirement.dataset_group()
            if group not in groups:
                groups.append(group)
        return tuple(groups)


@dataclass(frozen=True)
class DataflowProviderResult:
    provider_id: str
    dataset_groups: tuple[DatasetGroup, ...]
    status: CollectionStatus
    source_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    failure_reason: str | None = None
    rate_limit_hint: str | None = None
    started_at: datetime = field(default_factory=dataflow_now)
    completed_at: datetime | None = None

    def to_output(self) -> dict[str, object]:
        output: dict[str, object] = {
            "provider_id": self.provider_id,
            "dataset_groups": [group.value for group in self.dataset_groups],
            "status": self.status.value,
            "source_ids": list(self.source_ids),
            "warnings": list(self.warnings),
        }
        if self.failure_reason:
            output["failure_reason"] = self.failure_reason
        if self.rate_limit_hint:
            output["rate_limit_hint"] = self.rate_limit_hint
        return output


@dataclass(frozen=True)
class DataflowCollectionResult:
    collection_id: str
    market: Market
    symbol: str
    requested_dataset_groups: tuple[DatasetGroup, ...]
    provider_results: tuple[DataflowProviderResult, ...]
    records: tuple[CanonicalMarketDataRecord, ...]
    source_documents: tuple[SourceDocument, ...]
    status: CollectionStatus
    warnings: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    started_at: datetime = field(default_factory=dataflow_now)
    completed_at: datetime | None = None

    def to_output(self) -> dict[str, object]:
        return {
            "collection_id": self.collection_id,
            "status": self.status.value,
            "providers": sorted(
                {provider.provider_id for provider in self.provider_results}
            ),
            "requested_dataset_groups": [
                group.value for group in self.requested_dataset_groups
            ],
            "provider_results": [
                provider.to_output() for provider in self.provider_results
            ],
            "records_collected": len(self.records),
            "documents_collected": len(self.source_documents),
            "warnings": list(self.warnings),
            "failure_reasons": list(self.failure_reasons),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at is not None
            else None,
        }
