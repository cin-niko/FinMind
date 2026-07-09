from typing import Protocol

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Citation,
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

    def save_citations(self, run_id: str, citations: tuple[Citation, ...]) -> None: ...

    def list_citations(self, run_id: str) -> list[Citation]: ...

    def save_price_series(
        self,
        records: tuple[CanonicalMarketDataRecord, ...],
    ) -> None: ...

    def get(self, run_id: str) -> ExecutionRun | None: ...

    def list(self) -> list[ExecutionRun]: ...

    def delete(self, run_id: str) -> bool: ...

    def update_title(self, run_id: str, title: str) -> ExecutionRun | None: ...


class WorkflowRepository(Protocol):
    def list(self) -> list[WorkflowSpecification]: ...

    def get(self, workflow_id: str) -> WorkflowSpecification | None: ...
