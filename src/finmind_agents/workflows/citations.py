from finmind_agents.models import CanonicalMarketDataRecord, Citation


def build_citation(record: CanonicalMarketDataRecord) -> Citation:
    return Citation(
        citation_id=f"citation_{record.dataset_id}_{record.record_key}",
        source_id=record.source_id,
        dataset_id=record.dataset_id,
        label=f"{record.source_id} {record.market_time.date().isoformat()}",
        timestamp=record.market_time,
    )


def build_citations(
    records: tuple[CanonicalMarketDataRecord, ...],
) -> tuple[Citation, ...]:
    return tuple(build_citation(record) for record in records)
