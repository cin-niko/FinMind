from abc import ABC, abstractmethod

from pydantic import BaseModel, ValidationError

from ..chat import ToolSpec, ToolSpecFunction
from .exceptions import ToolInvocationError
from .interface import ITool
from .models import ToolResult


class BaseTool[T: BaseModel](ITool, ABC):
    arguments_model: type[T]

    def __init__(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> None:
        self._name = name
        self._description = description

    @property
    def input_model(self) -> type[T]:
        return type(self).arguments_model

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def parameters(self) -> dict[str, object]:
        return self.input_model.model_json_schema()

    def to_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            function=ToolSpecFunction(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
            )
        )

    async def ainvoke(self, arguments_json: str) -> ToolResult:
        try:
            arguments = self.input_model.model_validate_json(arguments_json or "{}")
        except ValidationError as exc:
            raise ToolInvocationError(
                f"Tool arguments for '{self.name}' must match the tool input schema."
            ) from exc

        return await self.run(arguments)

    @abstractmethod
    async def run(self, arguments: T) -> ToolResult:
        raise NotImplementedError
