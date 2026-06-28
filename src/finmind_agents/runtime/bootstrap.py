from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class AgentModelSettings:
    model: str | None = None
    api_key: str = ""
    api_base: str = ""
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "AgentModelSettings":
        return cls(
            model=os.getenv("LITELLM_CHAT_MODEL", "").strip() or None,
            api_key=os.getenv("LITELLM_API_KEY", "").strip(),
            api_base=os.getenv("LITELLM_API_BASE", "").strip(),
            temperature=float(os.getenv("FINMIND_AGENT_TEMPERATURE", "0")),
        )

    @property
    def configured(self) -> bool:
        return bool(self.model)


def build_chat_model(settings: AgentModelSettings) -> Any:
    if not settings.model:
        raise ValueError("LITELLM_CHAT_MODEL is required")

    from langchain_litellm import ChatLiteLLM

    provider_kwargs = {}
    if settings.api_base:
        provider_kwargs["custom_llm_provider"] = "openai"

    return ChatLiteLLM(
        model=settings.model,
        api_key=settings.api_key or None,
        api_base=settings.api_base or None,
        temperature=settings.temperature,
        **provider_kwargs,
    )
