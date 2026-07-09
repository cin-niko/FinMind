import asyncio
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_sync_offload_limit = 8
_sync_offload_semaphore: asyncio.Semaphore | None = None


def configure_sync_offload_limit(limit: int) -> None:
    global _sync_offload_limit, _sync_offload_semaphore
    _sync_offload_limit = max(1, limit)
    _sync_offload_semaphore = asyncio.Semaphore(_sync_offload_limit)


async def run_sync(callable_: Callable[..., T], /, *args: object) -> T:
    semaphore = _sync_offload_semaphore
    if semaphore is None:
        configure_sync_offload_limit(_sync_offload_limit)
        semaphore = _sync_offload_semaphore
    assert semaphore is not None
    async with semaphore:
        return await asyncio.to_thread(callable_, *args)
