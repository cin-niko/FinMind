from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from finmind_agents.models import utc_now


class StreamEventKind(StrEnum):
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STAGE = "workflow.stage"
    MESSAGE_DELTA = "message.delta"
    CITATION = "citation"
    ARTIFACT = "artifact"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"


@dataclass(frozen=True)
class StreamEvent:
    event_id: str
    conversation_id: str
    sequence: int
    kind: StreamEventKind
    created_at: str
    payload: dict[str, Any]

    @property
    def event_name(self) -> str:
        return self.kind.value

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "conversation_id": self.conversation_id,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "created_at": self.created_at,
            "payload": self.payload,
        }


def build_stream_event(
    conversation_id: str,
    sequence: int,
    kind: StreamEventKind,
    payload: dict[str, Any],
) -> StreamEvent:
    return StreamEvent(
        event_id=f"evt_{sequence:04d}",
        conversation_id=conversation_id,
        sequence=sequence,
        kind=kind,
        created_at=utc_now().isoformat(),
        payload=payload,
    )
