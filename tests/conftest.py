from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _in_memory_run_store(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Inject a fresh in-memory run repository for every test.

    The product run store is PostgreSQL; tests override the ``build_run_store``
    seam so the suite stays self-contained, fast, and offline. Each test gets a
    fresh repository so run state never leaks between tests.
    """
    from finmind_agents.memory import InMemoryRunRepository

    repo = InMemoryRunRepository()
    monkeypatch.setattr(
        "finmind_api.platform.build_run_store",
        lambda settings: repo,
    )
    yield
