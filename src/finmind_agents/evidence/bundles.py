from __future__ import annotations

from finmind_agents.data_records import (
    CompanyProfileRecord,
    DataBundle,
    DataRecord,
    FundamentalRecord,
    IndicatorsRecord,
    PatternEvidenceRecord,
    PatternSetupRecord,
    PriceSeriesRecord,
)
from finmind_agents.evidence.builders import mark_fundamentals_audited


def skill_data_bundle(skill_id: str, bundle: DataBundle) -> DataBundle:
    records: tuple[DataRecord, ...]
    if skill_id == "vn-technical-analysis":
        records = tuple(
            record
            for record in bundle.records
            if isinstance(
                record,
                (
                    IndicatorsRecord,
                    CompanyProfileRecord,
                    PatternEvidenceRecord,
                    PatternSetupRecord,
                ),
            )
        )
    else:
        records = tuple(
            record
            for record in bundle.records
            if isinstance(record, (FundamentalRecord, CompanyProfileRecord))
            or record.record_type == "price_summary"
        )
        if skill_id == "vn-fundamental-analysis":
            records = mark_fundamentals_audited(records)
    excluded_record_ids = tuple(
        record.record_id
        for record in bundle.records
        if isinstance(record, PriceSeriesRecord)
    )
    return DataBundle(
        records=records,
        bundle_id=f"{bundle.bundle_id}:{skill_id}",
        excluded_record_ids=excluded_record_ids,
    )
