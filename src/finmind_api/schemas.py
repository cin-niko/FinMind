from pydantic import BaseModel

from finmind_agents.serialization import serialize_run

__all__ = ["LoginRequest", "serialize_run"]


class LoginRequest(BaseModel):
    username: str
    password: str
