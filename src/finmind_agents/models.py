from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import cached_property
from typing import Any, ClassVar

from finmind_agents.evidence.rendering import render_record_context


class Market(StrEnum):
    VN_STOCK = "VN_STOCK"
    GOLD = "GOLD"


class ConversationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageSourceKind(StrEnum):
    WORKFLOW = "workflow_result"
    CHAT = "chat"


class WorkflowType(StrEnum):
    ATOMIC = "atomic"
    INTERNAL = "internal"
    COMPOSITE = "composite"


@dataclass(frozen=True)
class ChartRequirement:
    chart_id: str
    chart_type: str
    title: str
    source_types: tuple[str, ...]
    required: bool = True

    def to_output(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type,
            "title": self.title,
            "source_types": list(self.source_types),
            "required": self.required,
        }


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
    chart_requirements: tuple[ChartRequirement, ...]
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
class Citation:
    citation_id: str
    record_id: str
    record_type: str
    source_id: str
    dataset_id: str
    label: str
    timestamp: datetime
    instrument_id: str | None = None
    display_content: str | None = None
    payload_snapshot: dict[str, Any] = field(default_factory=dict)
    methodology_version: str | None = None


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
        return render_record_context(self.template_name, self.template_context())

    def to_prompt_record(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "dataset_id": self.dataset_id,
            "instrument_id": self.instrument_id,
            "market_time": self.market_time.isoformat(),
            "source_id": self.source_id,
            "citation_id": self.citation_id,
            "fields": _unavailable_for_prompt(self.payload),
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
class PatternEvidenceRecord(DataRecord):
    template_name: ClassVar[str | None] = "pattern_evidence.md.j2"


@dataclass(frozen=True)
class PatternSetupRecord(DataRecord):
    template_name: ClassVar[str | None] = "pattern_setup.md.j2"


@dataclass(frozen=True)
class FundamentalRecord(DataRecord):
    template_name: ClassVar[str | None] = "fundamentals.md.j2"


@dataclass(frozen=True)
class CompanyProfileRecord(DataRecord):
    template_name: ClassVar[str | None] = "company_profile.md.j2"


@dataclass(frozen=True)
class DataBundle:
    records: tuple[DataRecord, ...]
    bundle_id: str = "data_bundle"
    excluded_record_ids: tuple[str, ...] = ()

    def citation_ids(self) -> tuple[str, ...]:
        return tuple(record.citation_id for record in self.records)

    def by_citation_id(self) -> dict[str, DataRecord]:
        return {record.citation_id: record for record in self.records}

    def methodology_versions(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    record.methodology_version
                    for record in self.records
                    if record.methodology_version
                }
            )
        )

    def to_prompt_payload(self) -> dict[str, object]:
        return {
            "bundle_id": self.bundle_id,
            "records": [record.to_prompt_record() for record in self.records],
            "citation_ids": list(self.citation_ids()),
            "excluded_record_ids": list(self.excluded_record_ids),
            "methodology_versions": list(self.methodology_versions()),
        }


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    artifact_type: str
    title: str
    inputs: dict[str, Any]
    source_refs: tuple[str, ...]
    status: str = "ready"
    reason: str | None = None
    file_type: str | None = None
    file: dict[str, Any] | None = None
    mime_type: str | None = None
    chart_intent: str | None = None
    spec: dict[str, Any] | None = None
    downloads: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class WorkflowResult:
    """Transient, grounded output produced by a workflow before persistence.

    A workflow never writes user-facing history directly.  The conversation
    adapter below is the sole boundary that turns this result into a message.
    """

    workflow_id: str
    inputs: dict[str, object]
    sections: tuple[dict[str, object], ...]
    steps: tuple[dict[str, object], ...]
    collection: dict[str, object]
    citations: tuple[Citation, ...]
    artifacts: tuple[Artifact, ...]
    grounding: dict[str, object]
    language: str


@dataclass(frozen=True)
class Message:
    message_id: str
    conversation_id: str
    role: MessageRole
    source_kind: MessageSourceKind
    content: str
    created_at: datetime
    citations: tuple[Citation, ...] = ()
    artifacts: tuple[Artifact, ...] = ()
    workflow_id: str | None = None
    workflow_result: WorkflowResult | None = None


@dataclass(frozen=True)
class Conversation:
    conversation_id: str
    owner: str
    status: ConversationStatus
    title: str
    workflow_id: str | None
    inputs: dict[str, object]
    language: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    failure_message: str | None = None


def utc_now() -> datetime:
    return datetime.now(UTC)


def _unavailable_for_prompt(value: Any) -> Any:
    """Render absent evidence explicitly without mutating stored provenance."""
    if value is None:
        return "Unavailable"
    if isinstance(value, dict):
        return {key: _unavailable_for_prompt(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_unavailable_for_prompt(item) for item in value]
    if isinstance(value, tuple):
        return [_unavailable_for_prompt(item) for item in value]
    return value
