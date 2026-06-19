from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Market(StrEnum):
    VN_STOCK = "VN_STOCK"
    GOLD = "GOLD"


class FreshnessStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"
    FAILED = "failed"


class RunStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class AdminUser:
    username: str
    role: str = "admin"


@dataclass(frozen=True)
class Session:
    session_id: str
    username: str
    role: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class MarketInstrument:
    instrument_id: str
    symbol: str
    market: Market
    display_name: str
    currency: str
    status: str = "active"


@dataclass(frozen=True)
class CanonicalMarketDataRecord:
    dataset_id: str
    record_key: str
    instrument_id: str
    market_time: datetime
    collected_at: datetime
    source_id: str
    payload: dict[str, Any]
    freshness_status: FreshnessStatus = FreshnessStatus.FRESH


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    source_id: str
    title: str
    published_at: datetime
    collected_at: datetime
    url_or_reference: str
    content_excerpt: str
    market_scope: Market


@dataclass(frozen=True)
class WorkflowSpecification:
    workflow_id: str
    title: str
    market_scope: tuple[Market, ...]
    required_inputs: tuple[dict[str, Any], ...]
    stages: tuple[str, ...]
    role_agents: tuple[str, ...]
    output_sections: tuple[str, ...]
    citation_policy: str
    chart_requirements: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceObject:
    evidence_id: str
    claim_ref: str
    source_refs: tuple[str, ...]
    observed_at: datetime
    freshness_status: FreshnessStatus
    summary: str


@dataclass(frozen=True)
class Citation:
    citation_id: str
    evidence_id: str
    label: str
    source_type: str
    source_reference: str
    timestamp: datetime


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    artifact_type: str
    title: str
    inputs: dict[str, Any]
    payload: dict[str, Any]
    evidence_refs: tuple[str, ...]


@dataclass
class ExecutionRun:
    run_id: str
    kind: str
    status: RunStatus
    requested_by: str
    inputs: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    output: dict[str, Any]
    logs: list[dict[str, Any]] = field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(UTC)
