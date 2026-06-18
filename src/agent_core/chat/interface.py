from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from pydantic import BaseModel

from ..typedefs.messages import ChatOptions, Message, StreamEvent


class IChatModel(ABC):
    @abstractmethod
    async def chat(self, messages: list[Message], options: ChatOptions) -> Message:
        raise NotImplementedError

    @abstractmethod
    def stream(
        self, messages: list[Message], options: ChatOptions
    ) -> AsyncGenerator[StreamEvent, None]:
        raise NotImplementedError

    @abstractmethod
    async def parse[T: BaseModel](
        self, messages: list[Message], response_format: type[T], options: ChatOptions
    ) -> T:
        raise NotImplementedError
