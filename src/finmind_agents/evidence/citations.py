from __future__ import annotations

from finmind_agents.data_records import DataRecord
from finmind_agents.models import Citation


def build_citation_snapshot(record: DataRecord) -> dict[str, object]:
    return record.to_citation_snapshot()


def build_citation(record: DataRecord) -> Citation:
    return Citation(
        citation_id=record.citation_id,
        record_id=record.record_id,
        record_type=record.record_type,
        source_id=record.source_id,
        dataset_id=record.dataset_id,
        label=record.label,
        timestamp=record.market_time,
        instrument_id=record.instrument_id,
        display_content=record.context,
        payload_snapshot=build_citation_snapshot(record),
        methodology_version=record.methodology_version,
    )


def build_citations(records: tuple[DataRecord, ...]) -> tuple[Citation, ...]:
    return tuple(build_citation(record) for record in records)


def build_citation_allowlist(records: tuple[DataRecord, ...]) -> tuple[str, ...]:
    return tuple(record.citation_id for record in records)
