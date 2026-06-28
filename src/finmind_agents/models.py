from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Market(StrEnum):
    VN_STOCK = "VN_STOCK"
    US_STOCK = "US_STOCK"


class RunStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class WorkflowType(StrEnum):
    ATOMIC = "atomic"
    INTERNAL = "internal"
    COMPOSITE = "composite"


class WorkflowStepStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


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
    instrument_ids: tuple[str, ...] = ()
    sentiment_hint: str | None = None


@dataclass(frozen=True)
class WorkflowSpecification:
    workflow_id: str
    definition_path: str
    version: str
    title: str
    description: str
    workflow_type: WorkflowType
    market_scope: tuple[Market, ...]
    required_inputs: tuple[dict[str, Any], ...]
    stages: tuple[str, ...]
    skill_refs: tuple[str, ...]
    output_sections: tuple[str, ...]
    citation_policy: str
    chart_requirements: tuple[str, ...]
    step_sequence: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentSkill:
    skill_id: str
    skill_path: str
    version: str
    purpose: str
    required_context: tuple[str, ...]
    allowed_claims: tuple[str, ...]
    blocked_behavior: str
    output_contract: str
    citation_policy: str
    safety_rules: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    title: str
    kind: str
    status: WorkflowStepStatus
    blocking_issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Citation:
    citation_id: str
    source_id: str
    dataset_id: str
    label: str
    timestamp: datetime


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    artifact_type: str
    title: str
    inputs: dict[str, Any]
    payload: dict[str, Any]
    source_refs: tuple[str, ...]


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
