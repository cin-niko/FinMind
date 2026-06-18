from typing import Protocol

from pydantic import BaseModel

from ..chat import ToolSpec
from .models import ToolResult


class ITool(Protocol):
    @property
    def input_model(self) -> type[BaseModel]: ...

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str | None: ...

    @property
    def parameters(self) -> dict[str, object]: ...

    def to_tool_spec(self) -> ToolSpec: ...

    async def ainvoke(self, arguments_json: str) -> ToolResult: ...
