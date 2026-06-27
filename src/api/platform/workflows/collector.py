from dataclasses import dataclass

from api.platform.models import (
    CanonicalMarketDataRecord,
    Market,
    SourceDocument,
    WorkflowSpecification,
)
from api.platform.repositories import MarketDataRepository
from api.platform.workflows.validation import WorkflowValidationError


@dataclass(frozen=True)
class CollectedWorkflowData:
    records: tuple[CanonicalMarketDataRecord, ...]
    source_documents: tuple[SourceDocument, ...]


def collect_workflow_data(
    workflow: WorkflowSpecification,
    market_data: MarketDataRepository,
    market: Market,
    symbol: str | None,
) -> CollectedWorkflowData:
    records = [
        record
        for record in market_data.list_by_market(market)
        if _record_matches_required_datasets(record, workflow.required_datasets)
    ]
    if symbol:
        records = [record for record in records if record.instrument_id == symbol]
    source_documents = ()
    if "source_documents" in workflow.required_datasets:
        source_documents = tuple(market_data.list_source_documents(market, symbol))
    if not records and not source_documents:
        raise WorkflowValidationError("Required market data is missing")
    return CollectedWorkflowData(records=tuple(records), source_documents=source_documents)


def _record_matches_required_datasets(
    record: CanonicalMarketDataRecord,
    required_datasets: tuple[str, ...],
) -> bool:
    return (
        "price_series" in required_datasets
        and record.dataset_id.endswith("_prices")
        or "fundamentals" in required_datasets
        and record.dataset_id.endswith("_fundamentals")
    )
