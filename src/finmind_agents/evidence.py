from finmind_agents.models import CanonicalMarketDataRecord, Citation, EvidenceObject


def build_evidence(record: CanonicalMarketDataRecord, claim_ref: str) -> EvidenceObject:
    return EvidenceObject(
        evidence_id=f"evidence_{record.record_key}",
        claim_ref=claim_ref,
        source_refs=(record.record_key,),
        observed_at=record.market_time,
        freshness_status=record.freshness_status,
        summary=f"{record.dataset_id} record {record.record_key} supports {claim_ref}",
    )


def build_citation(record: CanonicalMarketDataRecord, evidence: EvidenceObject) -> Citation:
    return Citation(
        citation_id=f"citation_{record.record_key}",
        evidence_id=evidence.evidence_id,
        label=f"{record.source_id} {record.market_time.date().isoformat()}",
        source_type="market_data",
        source_reference=record.record_key,
        timestamp=record.market_time,
    )
