from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from finmind_agents.models import utc_now


class StreamEventKind(StrEnum):
    RUN_STARTED = "run.started"
    RUN_STAGE = "run.stage"
    ANSWER_DELTA = "answer.delta"
    CITATION = "citation"
    ARTIFACT = "artifact"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"


@dataclass(frozen=True)
class StreamEvent:
    event_id: str
    run_id: str
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
            "run_id": self.run_id,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "created_at": self.created_at,
            "payload": self.payload,
        }


def build_stream_event(
    run_id: str,
    sequence: int,
    kind: StreamEventKind,
    payload: dict[str, Any],
) -> StreamEvent:
    return StreamEvent(
        event_id=f"evt_{sequence:04d}",
        run_id=run_id,
        sequence=sequence,
        kind=kind,
        created_at=utc_now().isoformat(),
        payload=payload,
    )
