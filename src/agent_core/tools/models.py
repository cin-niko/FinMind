from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    content: str
    artifacts: dict[str, object] = Field(default_factory=dict)
