from typing import Protocol

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Citation,
    Market,
    SourceDocument,
    WorkflowSpecification,
    Conversation,
    ConversationStatus,
    Message,
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


class ConversationRepository(Protocol):
    """Persistence boundary for the user-visible conversation model."""

    def save_conversation(self, conversation: Conversation) -> None: ...

    def get_conversation(self, conversation_id: str, owner: str) -> Conversation | None: ...

    def list_conversations(self, owner: str) -> list[Conversation]: ...

    def update_conversation_status(
        self,
        conversation_id: str,
        owner: str,
        status: ConversationStatus,
        *,
        failure_message: str | None = None,
    ) -> Conversation | None: ...

    def save_message(self, message: Message) -> None: ...

    def list_messages(self, conversation_id: str, owner: str) -> list[Message]: ...

    def delete_conversation(self, conversation_id: str, owner: str) -> bool: ...

    def save_price_series(
        self,
        records: tuple[CanonicalMarketDataRecord, ...],
    ) -> None: ...

    def reconcile_interrupted(self) -> int: ...

    def get_language_preference(self, owner: str) -> str | None: ...

    def save_language_preference(self, owner: str, selection: str) -> str: ...


class WorkflowRepository(Protocol):
    def list(self) -> list[WorkflowSpecification]: ...

    def get(self, workflow_id: str) -> WorkflowSpecification | None: ...
