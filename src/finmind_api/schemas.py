from pydantic import BaseModel

from finmind_agents.serialization import serialize_run

__all__ = ["CitationResponse", "LoginRequest", "serialize_run"]


class LoginRequest(BaseModel):
    username: str
    password: str


class CitationResponse(BaseModel):
    citation_id: str
    record_id: str
    record_type: str
    source_id: str
    dataset_id: str
    label: str
    timestamp: str
    instrument_id: str | None = None
    display_content: str | None = None
    payload_snapshot: dict[str, object]
    methodology_version: str | None = None
