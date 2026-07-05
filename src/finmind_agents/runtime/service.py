import json
import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Protocol

from finmind_agents.runtime.bootstrap import AgentModelSettings, build_chat_model
from finmind_agents.runtime.models import AgentRuntimePolicy, RuntimeMode

from finmind_agents.agents.models import (
    AgentMetadataResult,
    AgentRunRequest,
    AgentRunResult,
    AgentStreamEvent,
)
from finmind_agents.agents.prompts import (
    ANSWER_STREAM_SYSTEM_PROMPT,
    METADATA_SYSTEM_PROMPT,
    build_skill_answer_prompt,
    build_skill_metadata_prompt,
)
from finmind_agents.agents.validators import (
    AgentValidationError,
    validate_agent_content,
    validate_agent_metadata,
    validate_agent_result,
)


class RuntimeConfigurationError(RuntimeError):
    """Raised when the configured runtime cannot satisfy its policy."""


class AgentOrchestratorError(RuntimeError):
    """Raised when skill execution cannot produce a valid agent result."""


class DeepAgent(Protocol):
    def invoke(self, input: dict[str, object]) -> object: ...


type DeepAgentFactory = Callable[
    [str, str, Callable[[str], str], bool],
    DeepAgent,
]


@dataclass(frozen=True)
class FinMindAgentRuntime:
    model_settings: AgentModelSettings
    policy: AgentRuntimePolicy

    def ensure_configured(self, mode: RuntimeMode) -> None:
        if mode != self.policy.mode:
            raise RuntimeConfigurationError(
                f"Runtime policy {self.policy.policy_id} does not allow {mode.value}"
            )
        if mode is RuntimeMode.WORKFLOW and not self.model_settings.configured:
            raise RuntimeConfigurationError(
                "LITELLM_CHAT_MODEL is required to run workflow agent skills"
            )


@dataclass(frozen=True)
class AgentOrchestrator:
    settings: AgentModelSettings | None = None
    agent_factory: DeepAgentFactory | None = None

    async def stream_skill(self, request: AgentRunRequest) -> AsyncIterator[AgentStreamEvent]:
        settings = self.settings or AgentModelSettings.from_env()
        runtime = FinMindAgentRuntime(
            model_settings=settings,
            policy=AgentRuntimePolicy.workflow_strict(allowed_skills=(request.skill_id,)),
        )
        try:
            runtime.ensure_configured(RuntimeMode.WORKFLOW)
        except RuntimeConfigurationError as error:
            raise AgentOrchestratorError(str(error)) from error

        if settings.model is None:
            raise AgentOrchestratorError(
                "LITELLM_CHAT_MODEL is required to run workflow agent skills"
            )

        factory = self.agent_factory or build_deep_agent
        skill_loader: Callable[[str], str] = lambda skill_id: (
            request.skill_markdown
            if skill_id == request.skill_id
            else f"Unknown skill: {skill_id}"
        )

        answer_parts: list[str] = []
        try:
            agent = factory(
                settings.model,
                ANSWER_STREAM_SYSTEM_PROMPT,
                skill_loader,
                _supports_agent_tools(settings.model),
            )
            run_stream = await agent.astream_events(
                {
                    "messages": [
                        {"role": "user", "content": build_skill_answer_prompt(request)}
                    ]
                },
                version="v3",
            )
            async with run_stream as run:
                async for chat_stream in run.messages:
                    async for delta in chat_stream.text:
                        if delta:
                            answer_parts.append(delta)
                            yield AgentStreamEvent(
                                kind="content_delta",
                                text=delta,
                            )
        except Exception as error:
            if isinstance(error, AgentOrchestratorError):
                raise
            raise AgentOrchestratorError(
                "Workflow agent skill execution failed: "
                f"{type(error).__name__}: {_safe_error_summary(error)}"
            ) from error

        answer_text = "".join(answer_parts).strip()
        if not answer_text:
            raise AgentOrchestratorError("Workflow agent returned empty content")
        validate_agent_content(answer_text)

        model = build_chat_model(settings)
        try:
            metadata = await _collect_streamed_metadata(model, request, answer_text)
            result = AgentRunResult(
                status=metadata.status,
                section_title=request.skill_id,
                content=answer_text,
                citations=metadata.citations,
                allowed_claims=metadata.allowed_claims,
                blocked_claims=metadata.blocked_claims,
                warnings=metadata.warnings,
            )
            validate_agent_result(result, request.citation_ids)
        except AgentValidationError as error:
            raise AgentOrchestratorError(str(error)) from error
        except Exception as error:
            if isinstance(error, AgentOrchestratorError):
                raise
            raise AgentOrchestratorError(
                "Workflow agent skill execution failed: "
                f"{type(error).__name__}: {_safe_error_summary(error)}"
            ) from error

        yield AgentStreamEvent(kind="result", result=result)


def build_deep_agent(
    model: str,
    system_prompt: str,
    skill_loader: Callable[[str], str],
    use_tools: bool,
) -> DeepAgent:
    from deepagents import create_deep_agent

    env_settings = AgentModelSettings.from_env()
    tools = []
    if use_tools:
        from langchain_core.tools import tool

        @tool
        def load_skill(skill_id: str) -> str:
            """Load the governed FinMind workflow skill by skill id."""
            return skill_loader(skill_id)

        tools.append(load_skill)

    return create_deep_agent(
        model=build_chat_model(
            AgentModelSettings(
                model=model,
                api_key=env_settings.api_key,
                api_base=env_settings.api_base,
            )
        ),
        tools=tools,
        system_prompt=system_prompt,
    )


def _supports_agent_tools(model: str) -> bool:
    normalized = model.lower()
    return not (
        normalized.startswith("cohere:")
        or normalized.startswith("cohere/")
        or normalized.startswith("command")
    )


def _content_from_agent_response(response: object) -> str | None:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        messages = response.get("messages")
        if isinstance(messages, list) and messages:
            return _message_content(messages[-1])
        content = response.get("content")
        return content if isinstance(content, str) else None
    return _message_content(response)


def _message_content(message: object) -> str | None:
    if isinstance(message, dict):
        content = message.get("content")
    else:
        content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return None


def _extract_json_object(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return stripped[start : end + 1]


async def _collect_streamed_metadata(
    model: object,
    request: AgentRunRequest,
    answer_text: str,
) -> AgentMetadataResult:
    from langchain_core.messages import HumanMessage, SystemMessage

    ainvoke = getattr(model, "ainvoke", None)
    if not callable(ainvoke):
        raise AgentOrchestratorError(
            "Workflow agent skill execution failed: model does not support async metadata finalization"
        )
    response = await ainvoke(
        [
            SystemMessage(content=METADATA_SYSTEM_PROMPT),
            HumanMessage(content=build_skill_metadata_prompt(request, answer_text)),
        ]
    )
    metadata = _agent_metadata_from_content(_content_from_agent_response(response))
    validate_agent_metadata(metadata, request.citation_ids)
    return metadata


def _agent_metadata_from_content(content: str | None) -> AgentMetadataResult:
    if not content:
        raise AgentOrchestratorError("Workflow agent returned empty metadata")
    try:
        payload = json.loads(_extract_json_object(content))
        return AgentMetadataResult.model_validate(payload)
    except (ValueError, json.JSONDecodeError) as error:
        raise AgentOrchestratorError("Workflow agent returned invalid metadata JSON") from error


def _safe_error_summary(error: Exception) -> str:
    summary = str(error).strip() or "no provider detail"
    summary = re.sub(
        r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+",
        r"\1<redacted>",
        summary,
    )
    summary = re.sub(
        r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?bearer\s+)[^\"'\s,}]+",
        r"\1<redacted>",
        summary,
    )
    return summary[:500]
