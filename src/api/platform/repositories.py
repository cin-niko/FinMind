from typing import Protocol

from api.platform.models import (
    CanonicalMarketDataRecord,
    ExecutionRun,
    Market,
    SourceDocument,
    WorkflowSpecification,
)


class MarketDataRepository(Protocol):
    def list_by_market(
        self,
        market: Market,
    ) -> list[CanonicalMarketDataRecord]: ...

    def list_source_documents(
        self,
        market: Market,
        symbol: str | None,
    ) -> list[SourceDocument]: ...


class RunRepository(Protocol):
    def save(self, run: ExecutionRun) -> None: ...

    def get(self, run_id: str) -> ExecutionRun | None: ...

    def list(self) -> list[ExecutionRun]: ...


class WorkflowRepository(Protocol):
    def list(self) -> list[WorkflowSpecification]: ...

    def get(self, workflow_id: str) -> WorkflowSpecification | None: ...
