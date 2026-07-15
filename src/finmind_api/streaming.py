import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass

from finmind_agents.streaming.models import StreamEvent


@dataclass(frozen=True)
class StreamLease:
    username: str


class StreamConcurrencyLimiter:
    def __init__(self, global_limit: int, per_user_limit: int) -> None:
        self._global_limit = max(1, global_limit)
        self._per_user_limit = max(1, per_user_limit)
        self._active_global = 0
        self._active_by_user: defaultdict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, username: str) -> StreamLease | None:
        async with self._lock:
            if self._active_global >= self._global_limit:
                return None
            if self._active_by_user[username] >= self._per_user_limit:
                return None
            self._active_global += 1
            self._active_by_user[username] += 1
            return StreamLease(username=username)

    async def release(self, lease: StreamLease) -> None:
        async with self._lock:
            self._active_global = max(0, self._active_global - 1)
            if self._active_by_user[lease.username] > 0:
                self._active_by_user[lease.username] -= 1
            if self._active_by_user[lease.username] == 0:
                self._active_by_user.pop(lease.username, None)


def encode_sse_event(event_name: str, payload: dict[str, object]) -> bytes:
    return (
        f"event: {event_name}\n"
        f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"
    ).encode("utf-8")


HEARTBEAT_FRAME = b": heartbeat\n\n"


async def sse_event_stream(event_source: AsyncIterator[object]) -> AsyncIterator[bytes]:
    async for event in event_source:
        if isinstance(event, StreamEvent):
            yield encode_sse_event(event.event_name, event.to_payload())
            continue
        to_payload = getattr(event, "to_payload", None)
        payload = to_payload() if callable(to_payload) else getattr(event, "payload")
        yield encode_sse_event(getattr(event, "event_name"), payload)


async def with_heartbeats(
    frame_source: AsyncIterator[bytes],
    interval: float,
) -> AsyncIterator[bytes]:
    """Yield SSE frames, emitting keepalive comment frames when idle.

    SSE comment lines (``: heartbeat``) are ignored by ``EventSource`` clients
    but keep the HTTP connection alive during long model phases (e.g. a
    reasoning model's pre-answer phase) so proxies and browsers do not close
    the stream. A non-positive ``interval`` disables heartbeats.
    """
    if interval <= 0:
        async for frame in frame_source:
            yield frame
        return

    aiter = frame_source.__aiter__()
    next_frame = asyncio.ensure_future(aiter.__anext__())
    while True:
        heartbeat = asyncio.ensure_future(asyncio.sleep(interval))
        done, _pending = await asyncio.wait(
            {next_frame, heartbeat},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if next_frame not in done:
            yield HEARTBEAT_FRAME
            await heartbeat
            continue
        heartbeat.cancel()
        try:
            await heartbeat
        except asyncio.CancelledError:
            pass
        try:
            frame = next_frame.result()
        except StopAsyncIteration:
            break
        yield frame
        next_frame = asyncio.ensure_future(aiter.__anext__())
