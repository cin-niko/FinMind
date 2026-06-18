from typing import Any, Self

from ...settings.litellm import LiteLLMSettings
from ..interface import IEmbeddingsModel


class EmbeddingsLiteLLMError(Exception):
    """Base error for LiteLLM embeddings adapter failures."""


class EmbeddingsLiteLLM(IEmbeddingsModel):
    def __init__(self, settings: LiteLLMSettings | None = None) -> None:
        self._settings = settings or LiteLLMSettings()

    @classmethod
    def from_settings(cls, settings: LiteLLMSettings | None = None) -> Self:
        return cls(settings=settings)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._aembedding(**self._build_request(texts))
        response_payload = self._as_mapping(response)
        data = response_payload.get("data", [])
        return [
            item["embedding"]
            for item in sorted(
                (self._as_mapping(raw_item) for raw_item in data),
                key=lambda item: item.get("index", 0),
            )
        ]

    def _build_request(self, texts: list[str]) -> dict[str, Any]:
        model = self._settings.embedding_model
        if model is None:
            raise EmbeddingsLiteLLMError(
                "Embedding model is required. Set LITELLM_EMBEDDING_MODEL."
            )
        payload: dict[str, Any] = {"model": model, "input": texts}
        if self._settings.api_key is not None:
            payload["api_key"] = self._settings.api_key
        if self._settings.api_base is not None:
            payload["api_base"] = self._settings.api_base
        if self._settings.api_version is not None:
            payload["api_version"] = self._settings.api_version
        return payload

    async def _aembedding(self, **kwargs: Any) -> Any:
        from litellm import aembedding  # type: ignore[import-not-found]

        return await aembedding(**kwargs)

    def _as_mapping(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        raise EmbeddingsLiteLLMError(f"Unsupported LiteLLM response object: {type(value).__name__}")
