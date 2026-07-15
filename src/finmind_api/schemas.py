from pydantic import BaseModel

__all__ = ["CitationResponse", "LoginRequest"]


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
