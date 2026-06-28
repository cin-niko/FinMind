import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from finmind_agents.runtime.bootstrap import AgentModelSettings, build_chat_model
from finmind_agents.runtime.models import AgentRuntimePolicy, RuntimeMode

from finmind_agents.agents.models import AgentRunRequest, AgentRunResult
from finmind_agents.agents.prompts import SYSTEM_PROMPT, build_skill_user_prompt
from finmind_agents.agents.validators import AgentValidationError, validate_agent_result


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

    runtime_adapter: str = "langchain_litellm"

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

    def run_skill(self, request: AgentRunRequest) -> AgentRunResult:
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
        try:
            agent = factory(
                settings.model,
                SYSTEM_PROMPT,
                lambda skill_id: request.skill_markdown
                if skill_id == request.skill_id
                else f"Unknown skill: {skill_id}",
                _supports_agent_tools(settings.model),
            )
            response = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": build_skill_user_prompt(request),
                        }
                    ]
                }
            )
            result = _agent_result_from_content(_content_from_agent_response(response))
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
        return result


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


def _agent_result_from_content(content: str | None) -> AgentRunResult:
    if not content:
        raise AgentOrchestratorError("Workflow agent returned empty content")
    try:
        payload = json.loads(_extract_json_object(content))
        if isinstance(payload, dict) and not isinstance(payload.get("content"), str):
            payload["content"] = json.dumps(
                payload.get("content"),
                ensure_ascii=True,
                indent=2,
                default=str,
            )
        return AgentRunResult.model_validate(payload)
    except (ValueError, json.JSONDecodeError) as error:
        raise AgentOrchestratorError("Workflow agent returned invalid JSON") from error


def _extract_json_object(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return stripped[start : end + 1]


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
