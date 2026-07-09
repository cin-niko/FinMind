from __future__ import annotations

from dataclasses import replace
from typing import Any

from finmind_agents.data_records import (
    CompanyProfileRecord,
    DataBundle,
    DataRecord,
    FundamentalRecord,
    IndicatorsRecord,
    PatternEvidenceRecord,
    PatternSetupRecord,
    PriceSeriesRecord,
    PriceSummaryRecord,
    build_data_record,
)
from finmind_agents.evidence.patterns import detect_pattern_evidence, detect_pattern_setups
from finmind_agents.models import CanonicalMarketDataRecord


def build_data_bundle(records: tuple[CanonicalMarketDataRecord, ...]) -> DataBundle:
    built: list[DataRecord] = [build_data_record(record) for record in records]
    price_record = next(
        (record for record in built if isinstance(record, PriceSeriesRecord)),
        None,
    )
    if price_record is not None and price_record.payload.get("series"):
        summary = build_price_summary_record(price_record)
        if summary is not None:
            built.append(summary)
        built.append(build_pattern_evidence_record(price_record))
        built.append(build_pattern_setup_record(price_record))
    return DataBundle(records=tuple(built))


def build_price_summary_record(price_record: PriceSeriesRecord) -> PriceSummaryRecord | None:
    series = price_record.payload.get("series", [])
    by_year: dict[int, dict[str, Any]] = {}
    for bar in series:
        date_str = bar.get("date", "")
        if len(date_str) < 4:
            continue
        year = int(date_str[:4])
        existing = by_year.get(year)
        if existing is None or date_str > existing["date"]:
            by_year[year] = bar
    year_end_bars = sorted(by_year.values(), key=lambda bar: bar["date"])
    if not year_end_bars:
        return None
    return PriceSummaryRecord(
        record_id=f"{price_record.dataset_id}:{price_record.instrument_id}-year-end",
        record_type="price_summary",
        dataset_id=price_record.dataset_id,
        instrument_id=price_record.instrument_id,
        market_time=price_record.market_time,
        collected_at=price_record.collected_at,
        source_id=price_record.source_id,
        payload={
            "year_end_prices": [
                {"date": bar["date"], "close": bar["close"], "volume": bar.get("volume")}
                for bar in year_end_bars
            ],
        },
        citation_id=price_record.citation_id,
        label=price_record.label,
        source_record_key=price_record.source_record_key,
    )


def build_pattern_evidence_record(price_record: PriceSeriesRecord) -> PatternEvidenceRecord:
    return PatternEvidenceRecord(
        record_id=f"{price_record.dataset_id}:{price_record.instrument_id}-pattern-evidence",
        record_type="pattern_evidence",
        dataset_id=price_record.dataset_id,
        instrument_id=price_record.instrument_id,
        market_time=price_record.market_time,
        collected_at=price_record.collected_at,
        source_id=price_record.source_id,
        payload=detect_pattern_evidence(price_record.payload["series"]),
        citation_id=f"{price_record.citation_id}_pattern_evidence",
        label=f"{price_record.label} pattern evidence",
        source_record_key=price_record.source_record_key,
        methodology_version="pattern_detection.v1",
    )


def build_pattern_setup_record(price_record: PriceSeriesRecord) -> PatternSetupRecord:
    return PatternSetupRecord(
        record_id=f"{price_record.dataset_id}:{price_record.instrument_id}-pattern-setup",
        record_type="pattern_setup",
        dataset_id=price_record.dataset_id,
        instrument_id=price_record.instrument_id,
        market_time=price_record.market_time,
        collected_at=price_record.collected_at,
        source_id=price_record.source_id,
        payload=detect_pattern_setups(price_record.payload["series"]),
        citation_id=f"{price_record.citation_id}_pattern_setup",
        label=f"{price_record.label} pattern setups",
        source_record_key=price_record.source_record_key,
        methodology_version="pattern_scoring.v1",
    )


def mark_fundamentals_audited(records: tuple[DataRecord, ...]) -> tuple[DataRecord, ...]:
    audited: list[DataRecord] = []
    for record in records:
        if isinstance(record, FundamentalRecord):
            payload = dict(record.payload)
            payload["is_audited"] = True
            payload.setdefault("audit_warnings", [])
            audited.append(replace(record, payload=payload))
        else:
            audited.append(record)
    return tuple(audited)
