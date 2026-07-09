from __future__ import annotations

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    CompanyProfileRecord,
    DataBundle,
    DataRecord,
    FundamentalRecord,
    IndicatorsRecord,
    PatternEvidenceRecord,
    PatternSetupRecord,
    PriceSeriesRecord,
    PriceSummaryRecord,
)


def build_data_record(record: CanonicalMarketDataRecord) -> DataRecord:
    citation_id = f"citation_{record.dataset_id}_{record.record_key}"
    label = f"{record.source_id} {record.market_time.date().isoformat()}"
    base_kwargs = {
        "record_id": f"{record.dataset_id}:{record.record_key}",
        "dataset_id": record.dataset_id,
        "instrument_id": record.instrument_id,
        "market_time": record.market_time,
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "payload": record.payload,
        "citation_id": citation_id,
        "label": label,
        "source_record_key": record.record_key,
    }
    if record.dataset_id.endswith("_prices"):
        return PriceSeriesRecord(record_type="price_series", **base_kwargs)
    if record.dataset_id.endswith("_fundamentals"):
        payload = dict(record.payload)
        payload.setdefault("is_audited", False)
        payload.setdefault("audit_warnings", ["audit_not_run"])
        fundamental_kwargs = dict(base_kwargs)
        fundamental_kwargs["payload"] = payload
        return FundamentalRecord(record_type="fundamental", **fundamental_kwargs)
    if record.dataset_id.endswith("_company_profile"):
        return CompanyProfileRecord(record_type="company_profile", **base_kwargs)
    if record.dataset_id.endswith("_indicators") or record.dataset_id == "vn_indicators":
        return IndicatorsRecord(
            record_type="indicator",
            methodology_version="indicators.v1",
            **base_kwargs,
        )
    return DataRecord(record_type="generic", **base_kwargs)


def build_data_bundle(records: tuple[CanonicalMarketDataRecord, ...]) -> DataBundle:
    return DataBundle(records=tuple(build_data_record(record) for record in records))
