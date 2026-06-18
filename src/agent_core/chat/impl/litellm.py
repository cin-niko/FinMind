from collections.abc import AsyncGenerator
from typing import Any, Self

from pydantic import BaseModel

from ...settings.litellm import LiteLLMSettings
from ...typedefs import (
    ChatOptions,
    Message,
    MessageCompletedEvent,
    MessageRole,
    MessageStartEvent,
    StreamEvent,
    TextDeltaEvent,
    ToolCall,
    ToolCallCompletedEvent,
    ToolCallDeltaEvent,
    ToolCallFunction,
    ToolSpec,
    Usage,
    UsageEvent,
)
from ..interface import IChatModel


class ChatLiteLLMError(Exception):
    """Base error for LiteLLM chat adapter failures."""


class ChatParseError(ChatLiteLLMError):
    """Raised when structured parsing does not return the requested model."""


class ChatResponsesLiteLLMError(ChatLiteLLMError):
    """Base error for LiteLLM Responses API adapter failures."""


class ChatLiteLLM(IChatModel):
    def __init__(self, settings: LiteLLMSettings | None = None) -> None:
        self._settings = settings or LiteLLMSettings()

    @classmethod
    def from_settings(
        cls,
        settings: LiteLLMSettings | None = None,
    ) -> Self:
        return cls(settings=settings)

    def _build_request(self, messages: list[Message], options: ChatOptions) -> dict[str, Any]:
        model = options.model or self._settings.chat_model
        if model is None:
            raise ChatLiteLLMError(
                "Chat model is required. Pass ChatOptions(model=...) or set " "LITELLM_CHAT_MODEL."
            )
        payload: dict[str, Any] = {
            "model": model,
            "messages": [self._message_to_litellm(message) for message in messages],
        }
        if self._settings.api_key is not None:
            payload["api_key"] = self._settings.api_key
        if self._settings.api_base is not None:
            payload["api_base"] = self._settings.api_base
        if self._settings.api_version is not None:
            payload["api_version"] = self._settings.api_version
        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.max_tokens is not None:
            payload["max_tokens"] = options.max_tokens
        if options.timeout is not None:
            payload["timeout"] = options.timeout
        if options.tools:
            payload["tools"] = [self._tool_to_litellm(tool) for tool in options.tools]
        if options.tool_choice is not None:
            payload["tool_choice"] = options.tool_choice
        return payload

    def _tool_to_litellm(self, tool: ToolSpec) -> dict[str, Any]:
        return tool.model_dump(exclude_none=True)

    def _message_to_litellm(self, message: Message) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": message.role.value}
        if message.content is not None:
            payload["content"] = message.content
        if message.name is not None:
            payload["name"] = message.name
        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments_json,
                    },
                }
                for call in message.tool_calls
            ]
        if message.tool_call_id is not None:
            payload["tool_call_id"] = message.tool_call_id
        return payload

    async def chat(self, messages: list[Message], options: ChatOptions) -> Message:
        response = await self._acompletion(**self._build_request(messages, options))
        return self._message_from_response(response)

    async def stream(
        self, messages: list[Message], options: ChatOptions
    ) -> AsyncGenerator[StreamEvent, None]:
        stream = await self._acompletion(**self._build_request(messages, options), stream=True)
        message = Message(role=MessageRole.ASSISTANT, content="")
        started = False
        tool_call_chunks: dict[int, dict[str, Any]] = {}

        async for raw_chunk in stream:
            chunk = self._as_mapping(raw_chunk)
            choice = self._as_mapping(chunk["choices"][0])
            delta = self._as_mapping(choice.get("delta", {}))

            if not started and (
                delta.get("role") == MessageRole.ASSISTANT.value
                or "content" in delta
                or "tool_calls" in delta
            ):
                started = True
                yield MessageStartEvent(message=message.model_copy())

            text_delta = delta.get("content")
            if text_delta:
                message.content = (message.content or "") + text_delta
                yield TextDeltaEvent(delta=text_delta)

            for tool_call_delta in delta.get("tool_calls", []):
                tool_call = self._merge_tool_call_delta(tool_call_chunks, tool_call_delta)
                if tool_call is not None:
                    yield ToolCallDeltaEvent(tool_call=tool_call)

            usage_payload = chunk.get("usage")
            if usage_payload is not None:
                yield UsageEvent(usage=self._usage_from_litellm(usage_payload))

            finish_reason = choice.get("finish_reason")
            if finish_reason is not None:
                message.finish_reason = finish_reason
                message.tool_calls = self._completed_tool_calls(tool_call_chunks)
                for tool_call in message.tool_calls:
                    yield ToolCallCompletedEvent(tool_call=tool_call)
                yield MessageCompletedEvent(message=message)

    async def parse[T: BaseModel](
        self, messages: list[Message], response_format: type[T], options: ChatOptions
    ) -> T:
        response = await self._acompletion(
            **self._build_request(messages, options),
            response_format=response_format,
        )
        if isinstance(response, response_format):
            return response
        raise ChatParseError("LiteLLM did not return an instance of the requested response_format.")

    async def _acompletion(self, **kwargs: Any) -> Any:
        from litellm import acompletion  # type: ignore[import-not-found]

        return await acompletion(**kwargs)

    def _message_from_response(self, response: Any) -> Message:
        response_payload = self._as_mapping(response)
        choices = response_payload["choices"]
        choice = self._as_mapping(choices[0])
        raw_message = self._as_mapping(choice["message"])
        usage_payload = response_payload.get("usage")

        return Message(
            role=MessageRole(raw_message["role"]),
            content=raw_message.get("content"),
            tool_calls=[
                self._tool_call_from_litellm(item) for item in (raw_message.get("tool_calls") or [])
            ],
            finish_reason=choice.get("finish_reason"),
            usage=self._usage_from_litellm(usage_payload) if usage_payload is not None else None,
        )

    def _tool_call_from_litellm(self, raw_tool_call: Any) -> ToolCall:
        tool_call = self._as_mapping(raw_tool_call)
        function = self._as_mapping(tool_call["function"])
        return ToolCall(
            id=tool_call["id"],
            type=tool_call.get("type", "function"),
            function=ToolCallFunction(
                name=function["name"],
                arguments_json=function["arguments"],
            ),
        )

    def _merge_tool_call_delta(
        self,
        tool_call_chunks: dict[int, dict[str, Any]],
        raw_tool_call_delta: Any,
    ) -> ToolCall | None:
        delta = self._as_mapping(raw_tool_call_delta)
        index = delta.get("index", 0)
        current = tool_call_chunks.setdefault(index, {"function": {"arguments": ""}})

        if delta.get("id") is not None:
            current["id"] = delta["id"]
        if delta.get("type") is not None:
            current["type"] = delta["type"]

        function_delta = self._as_mapping(delta.get("function", {}))
        function = current.setdefault("function", {"arguments": ""})
        if function_delta.get("name") is not None:
            function["name"] = function_delta["name"]
        if function_delta.get("arguments") is not None:
            function["arguments"] = function.get("arguments", "") + function_delta["arguments"]

        return self._tool_call_from_partial(current)

    def _completed_tool_calls(self, tool_call_chunks: dict[int, dict[str, Any]]) -> list[ToolCall]:
        return [
            tool_call
            for _, current in sorted(tool_call_chunks.items())
            if (tool_call := self._tool_call_from_partial(current)) is not None
        ]

    def _tool_call_from_partial(self, raw_tool_call: dict[str, Any]) -> ToolCall | None:
        function = self._as_mapping(raw_tool_call.get("function", {}))
        if raw_tool_call.get("id") is None or function.get("name") is None:
            return None
        return ToolCall(
            id=raw_tool_call["id"],
            type=raw_tool_call.get("type", "function"),
            function=ToolCallFunction(
                name=function["name"],
                arguments_json=function.get("arguments", ""),
            ),
        )

    def _usage_from_litellm(self, raw_usage: Any) -> Usage:
        usage = self._as_mapping(raw_usage)
        return Usage(
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    def _as_mapping(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        raise ChatLiteLLMError(f"Unsupported LiteLLM response object: {type(value).__name__}")


class ChatResponsesLiteLLM(ChatLiteLLM):
    @classmethod
    def from_settings(
        cls,
        settings: LiteLLMSettings | None = None,
    ) -> Self:
        return cls(settings=settings)

    def _build_request(self, messages: list[Message], options: ChatOptions) -> dict[str, Any]:
        model = options.model or self._settings.chat_model
        if model is None:
            raise ChatResponsesLiteLLMError(
                "Chat model is required. Pass ChatOptions(model=...) or set " "LITELLM_CHAT_MODEL."
            )
        payload: dict[str, Any] = {
            "model": model,
            "input": self._messages_to_responses_input(messages),
        }
        if self._settings.api_key is not None:
            payload["api_key"] = self._settings.api_key
        if self._settings.api_base is not None:
            payload["api_base"] = self._settings.api_base
        if self._settings.api_version is not None:
            payload["api_version"] = self._settings.api_version
        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.max_tokens is not None:
            payload["max_output_tokens"] = options.max_tokens
        if options.timeout is not None:
            payload["timeout"] = options.timeout
        if options.tools:
            payload["tools"] = [self._tool_to_responses(tool) for tool in options.tools]
        if options.tool_choice is not None:
            payload["tool_choice"] = options.tool_choice
        return payload

    async def chat(self, messages: list[Message], options: ChatOptions) -> Message:
        response = await self._aresponses(**self._build_request(messages, options))
        return self._message_from_responses(response)

    async def stream(
        self, messages: list[Message], options: ChatOptions
    ) -> AsyncGenerator[StreamEvent, None]:
        stream = await self._aresponses(**self._build_request(messages, options), stream=True)
        message = Message(role=MessageRole.ASSISTANT, content="")
        started = False
        tool_call_chunks: dict[int, dict[str, Any]] = {}
        output_item_index = -1

        async for raw_event in stream:
            event = self._as_mapping(raw_event)
            event_type = event.get("type")

            if event_type == "response.output_item.added":
                item = self._as_mapping(event["item"])
                output_item_index += 1
                output_index = event.get("output_index", output_item_index)
                if item.get("type") == "message" and not started:
                    started = True
                    yield MessageStartEvent(message=message.model_copy())
                elif item.get("type") == "function_call":
                    tool_call_chunks[output_index] = {
                        "id": item.get("call_id"),
                        "type": "function",
                        "function": {
                            "name": item.get("name"),
                            "arguments": item.get("arguments", ""),
                        },
                    }
            elif event_type == "response.output_text.delta":
                text_delta = event.get("delta")
                if text_delta:
                    if not started:
                        started = True
                        yield MessageStartEvent(message=message.model_copy())
                    message.content = (message.content or "") + text_delta
                    yield TextDeltaEvent(delta=text_delta)
            elif event_type == "response.function_call_arguments.delta":
                output_index = event.get("output_index", 0)
                current = tool_call_chunks.setdefault(
                    output_index,
                    {"type": "function", "function": {"arguments": ""}},
                )
                function = current.setdefault("function", {"arguments": ""})
                function["arguments"] = function.get("arguments", "") + event.get("delta", "")
                if tool_call := self._tool_call_from_partial(current):
                    yield ToolCallDeltaEvent(tool_call=tool_call)
            elif event_type == "response.completed":
                completed_message = self._message_from_responses(event["response"])
                message.content = completed_message.content
                message.finish_reason = completed_message.finish_reason
                message.tool_calls = completed_message.tool_calls
                message.usage = completed_message.usage
                for tool_call in message.tool_calls:
                    yield ToolCallCompletedEvent(tool_call=tool_call)
                if message.usage is not None:
                    yield UsageEvent(usage=message.usage)
                yield MessageCompletedEvent(message=message)

    async def parse[T: BaseModel](
        self, messages: list[Message], response_format: type[T], options: ChatOptions
    ) -> T:
        response = await self._aresponses(
            **self._build_request(messages, options),
            text_format=response_format,
        )
        if isinstance(response, response_format):
            return response
        parsed = getattr(response, "output_parsed", None)
        if isinstance(parsed, response_format):
            return parsed
        raise ChatParseError("LiteLLM did not return an instance of the requested response_format.")

    async def _aresponses(self, **kwargs: Any) -> Any:
        from litellm import aresponses  # type: ignore[import-not-found]

        return await aresponses(**kwargs)

    def _messages_to_responses_input(self, messages: list[Message]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for message in messages:
            if message.role == MessageRole.TOOL:
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.tool_call_id,
                        "output": message.content or "",
                    }
                )
                continue

            if message.content is not None:
                items.append({"role": message.role.value, "content": message.content})

            if message.role == MessageRole.ASSISTANT:
                for tool_call in message.tool_calls:
                    items.append(
                        {
                            "type": "function_call",
                            "call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments_json,
                        }
                    )
        return items

    def _tool_to_responses(self, tool: ToolSpec) -> dict[str, Any]:
        return {
            "type": "function",
            "name": tool.function.name,
            "description": tool.function.description,
            "parameters": tool.function.parameters,
        }

    def _message_from_responses(self, response: Any) -> Message:
        response_payload = self._as_mapping(response)
        output_items = response_payload.get("output", [])
        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for raw_item in output_items:
            item = self._as_mapping(raw_item)
            item_type = item.get("type")
            if item_type == "message":
                for raw_content in item.get("content", []):
                    content = self._as_mapping(raw_content)
                    if content.get("type") == "output_text":
                        content_parts.append(content.get("text", ""))
            elif item_type == "function_call":
                tool_calls.append(
                    ToolCall(
                        id=item["call_id"],
                        function=ToolCallFunction(
                            name=item["name"],
                            arguments_json=item["arguments"],
                        ),
                    )
                )

        usage_payload = response_payload.get("usage")
        return Message(
            role=MessageRole.ASSISTANT,
            content="".join(content_parts) or None,
            tool_calls=tool_calls,
            finish_reason=response_payload.get("status"),
            usage=self._usage_from_litellm(usage_payload) if usage_payload is not None else None,
        )
