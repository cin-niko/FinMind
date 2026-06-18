from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallFunction(BaseModel):
    name: str
    arguments_json: str


class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: ToolCallFunction


class ToolSpecFunction(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, object] = Field(default_factory=dict)


class ToolSpec(BaseModel):
    type: Literal["function"] = "function"
    function: ToolSpecFunction


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class Message(BaseModel):
    role: MessageRole
    content: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None
    finish_reason: str | None = None
    usage: Usage | None = None


class ChatOptions(BaseModel):
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: float | None = None
    tools: list[ToolSpec] = Field(default_factory=list)
    tool_choice: str | dict[str, object] | None = None


class StreamEventType(str, Enum):
    MESSAGE_START = "message_start"
    TEXT_DELTA = "text_delta"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_COMPLETED = "tool_call_completed"
    MESSAGE_COMPLETED = "message_completed"
    USAGE = "usage"
    ERROR = "error"


class StreamEventBase(BaseModel):
    type: StreamEventType


class MessageStartEvent(StreamEventBase):
    type: Literal[StreamEventType.MESSAGE_START] = StreamEventType.MESSAGE_START
    message: Message


class TextDeltaEvent(StreamEventBase):
    type: Literal[StreamEventType.TEXT_DELTA] = StreamEventType.TEXT_DELTA
    delta: str


class ToolCallDeltaEvent(StreamEventBase):
    type: Literal[StreamEventType.TOOL_CALL_DELTA] = StreamEventType.TOOL_CALL_DELTA
    tool_call: ToolCall


class ToolCallCompletedEvent(StreamEventBase):
    type: Literal[StreamEventType.TOOL_CALL_COMPLETED] = StreamEventType.TOOL_CALL_COMPLETED
    tool_call: ToolCall


class MessageCompletedEvent(StreamEventBase):
    type: Literal[StreamEventType.MESSAGE_COMPLETED] = StreamEventType.MESSAGE_COMPLETED
    message: Message


class UsageEvent(StreamEventBase):
    type: Literal[StreamEventType.USAGE] = StreamEventType.USAGE
    usage: Usage


class ErrorEvent(StreamEventBase):
    type: Literal[StreamEventType.ERROR] = StreamEventType.ERROR
    error: str


type StreamEvent = Annotated[
    MessageStartEvent
    | TextDeltaEvent
    | ToolCallDeltaEvent
    | ToolCallCompletedEvent
    | MessageCompletedEvent
    | UsageEvent
    | ErrorEvent,
    Field(discriminator="type"),
]
