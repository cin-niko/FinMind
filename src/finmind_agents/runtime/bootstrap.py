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

    # OpenAI-compatible endpoints (LITELLM_API_BASE set) use langchain-openai
    # directly. langchain-litellm was found to buffer the streamed completion
    # into a single chunk for these endpoints, defeating token streaming;
    # ChatOpenAI forwards per-SSE deltas. Provider-routed models without an
    # explicit api_base (e.g. gemini/..., cohere/...) still go through
    # langchain-litellm.
    if settings.api_base:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key or None,
            base_url=settings.api_base,
            streaming=True,
            temperature=settings.temperature,
        )

    from langchain_litellm import ChatLiteLLM

    return ChatLiteLLM(
        model=settings.model,
        api_key=settings.api_key or None,
        api_base=settings.api_base or None,
        temperature=settings.temperature,
    )
