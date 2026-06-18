from abc import ABC, abstractmethod


class IEmbeddingsModel(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
