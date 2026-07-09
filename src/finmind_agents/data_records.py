from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
import json
from pathlib import Path
from typing import Any, ClassVar

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from finmind_agents.models import CanonicalMarketDataRecord

_TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_ROOT),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    template = _TEMPLATE_ENV.get_template(f"records/{template_name}")
    return template.render(**context).strip()


def _fallback_context(context: dict[str, Any]) -> str:
    payload = context.get("payload", {})
    return json.dumps(payload, ensure_ascii=True, indent=2, default=str)


@dataclass(frozen=True)
class DataRecord:
    record_id: str
    record_type: str
    dataset_id: str
    instrument_id: str
    market_time: datetime
    collected_at: datetime
    source_id: str
    payload: dict[str, Any]
    citation_id: str
    label: str
    source_record_key: str | None = None
    methodology_version: str | None = None

    template_name: ClassVar[str | None] = None

    def template_context(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "dataset_id": self.dataset_id,
            "instrument_id": self.instrument_id,
            "market_time": self.market_time.isoformat(),
            "collected_at": self.collected_at.isoformat(),
            "source_id": self.source_id,
            "citation_id": self.citation_id,
            "label": self.label,
            "source_record_key": self.source_record_key,
            "methodology_version": self.methodology_version,
            "payload": self.payload,
            **self.payload,
        }

    @cached_property
    def context(self) -> str:
        if self.template_name is None:
            return _fallback_context(self.template_context())
        return _render_template(self.template_name, self.template_context())

    def to_prompt_record(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "dataset_id": self.dataset_id,
            "instrument_id": self.instrument_id,
            "market_time": self.market_time.isoformat(),
            "source_id": self.source_id,
            "citation_id": self.citation_id,
            "fields": self.payload,
            "context": self.context,
        }

    def to_citation_snapshot(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "dataset_id": self.dataset_id,
            "instrument_id": self.instrument_id,
            "market_time": self.market_time.isoformat(),
            "source_id": self.source_id,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class PriceSeriesRecord(DataRecord):
    template_name: ClassVar[str | None] = "price_series.md.j2"


@dataclass(frozen=True)
class PriceSummaryRecord(DataRecord):
    template_name: ClassVar[str | None] = "price_summary.md.j2"


@dataclass(frozen=True)
class IndicatorsRecord(DataRecord):
    template_name: ClassVar[str | None] = "indicators.md.j2"


@dataclass(frozen=True)
class FundamentalRecord(DataRecord):
    template_name: ClassVar[str | None] = "fundamentals.md.j2"


@dataclass(frozen=True)
class CompanyProfileRecord(DataRecord):
    template_name: ClassVar[str | None] = "company_profile.md.j2"


@dataclass(frozen=True)
class DataBundle:
    records: tuple[DataRecord, ...]

    def citation_ids(self) -> tuple[str, ...]:
        return tuple(record.citation_id for record in self.records)

    def by_citation_id(self) -> dict[str, DataRecord]:
        return {record.citation_id: record for record in self.records}


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
        return FundamentalRecord(record_type="fundamental", **base_kwargs)
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
