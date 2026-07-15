from datetime import UTC, datetime

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Conversation,
    ConversationStatus,
    Market,
    Message,
    SourceDocument,
)
from finmind_agents.repositories import (
    ConversationRepository,
    MarketDataRepository,
)
from finmind_agents.workflows.catalog import build_workflow_catalog
from finmind_agents.workflows.specs import WorkflowCatalog


class InMemoryMarketDataRepository(MarketDataRepository):
    def __init__(self) -> None:
        collected_at = datetime(2026, 6, 18, 8, 0, tzinfo=UTC)
        self._records = [
            CanonicalMarketDataRecord(
                dataset_id="vn_prices",
                record_key="VNINDEX-prices",
                instrument_id="VNINDEX",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_prices",
                payload={
                    "series": [
                        {"date": "2026-06-18", "open": None, "high": None, "low": None,
                         "close": 1285.4, "change_percent": 0.82, "volume": 812000000},
                    ],
                    "count": 1,
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-18",
                    "interval": "1D",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="vn_prices",
                record_key="VCB-prices",
                instrument_id="VCB",
                market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_prices",
                payload={
                    "series": [
                        {"date": "2026-06-18", "open": None, "high": None, "low": None,
                         "close": 58200, "change_percent": 1.14, "volume": 4920000},
                    ],
                    "count": 1,
                    "start_date": "2026-06-18",
                    "end_date": "2026-06-18",
                    "interval": "1D",
                },
            ),
            CanonicalMarketDataRecord(
                dataset_id="vn_fundamentals",
                record_key="VCB-FY2025",
                instrument_id="VCB",
                market_time=datetime(2026, 3, 31, 7, 0, tzinfo=UTC),
                collected_at=collected_at,
                source_id="demo_vn_fundamentals",
                payload={
                    "eps": 5200,
                    "bvps": 35600,
                    "roe_percent": 20.3,
                    "period": "FY2025",
                },
            ),
        ]
        self._source_documents = [
            SourceDocument(
                document_id="doc_vcb_demo",
                source_id="demo_curated_sources",
                title="VCB curated company update",
                published_at=datetime(2026, 6, 18, 6, 30, tzinfo=UTC),
                collected_at=collected_at,
                url_or_reference="demo://vn/vcb/update",
                content_excerpt="Curated demo update for VCB banking fundamentals.",
                market_scope=Market.VN_STOCK,
                instrument_ids=("VCB",),
                sentiment_hint="neutral",
            ),
        ]

    def list_by_market(
        self,
        market: Market,
    ) -> list[CanonicalMarketDataRecord]:
        dataset_prefix_by_market = {Market.VN_STOCK: "vn_"}
        dataset_prefix = dataset_prefix_by_market[market]
        return [
            record
            for record in self._records
            if record.dataset_id.startswith(dataset_prefix)
        ]

    def list_source_documents(
        self,
        market: Market,
        symbol: str | None,
    ) -> list[SourceDocument]:
        return [
            document
            for document in self._source_documents
            if document.market_scope == market
            and (symbol is None or symbol in document.instrument_ids)
        ]


class InMemoryConversationRepository(ConversationRepository):
    """Deterministic repository used by tests and local fixture wiring."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, list[Message]] = {}
        self._price_series: dict[tuple[str, str], CanonicalMarketDataRecord] = {}
        self._language_preferences: dict[str, str] = {}

    def save_conversation(self, conversation: Conversation) -> None:
        self._conversations[conversation.conversation_id] = conversation

    def get_conversation(self, conversation_id: str, owner: str) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        return conversation if conversation and conversation.owner == owner else None

    def list_conversations(self, owner: str) -> list[Conversation]:
        return sorted(
            (
                conversation
                for conversation in self._conversations.values()
                if conversation.owner == owner
            ),
            key=lambda conversation: conversation.updated_at,
            reverse=True,
        )

    def update_conversation_status(
        self,
        conversation_id: str,
        owner: str,
        status: ConversationStatus,
        *,
        failure_message: str | None = None,
    ) -> Conversation | None:
        from dataclasses import replace

        conversation = self.get_conversation(conversation_id, owner)
        if conversation is None:
            return None
        now = datetime.now(UTC)
        updated = replace(
            conversation,
            status=status,
            updated_at=now,
            completed_at=now if status in {ConversationStatus.SUCCESS, ConversationStatus.FAILED} else None,
            failure_message=failure_message,
        )
        self._conversations[conversation_id] = updated
        return updated

    def save_message(self, message: Message) -> None:
        self._messages.setdefault(message.conversation_id, []).append(message)

    def list_messages(self, conversation_id: str, owner: str) -> list[Message]:
        if self.get_conversation(conversation_id, owner) is None:
            return []
        return sorted(
            self._messages.get(conversation_id, []),
            key=lambda message: message.created_at,
        )

    def delete_conversation(self, conversation_id: str, owner: str) -> bool:
        conversation = self.get_conversation(conversation_id, owner)
        if conversation is None or conversation.status not in {
            ConversationStatus.SUCCESS,
            ConversationStatus.FAILED,
        }:
            return False
        del self._conversations[conversation_id]
        self._messages.pop(conversation_id, None)
        return True

    def save_price_series(
        self,
        records: tuple[CanonicalMarketDataRecord, ...],
    ) -> None:
        for record in records:
            self._price_series[(record.dataset_id, record.record_key)] = record

    def reconcile_interrupted(self) -> int:
        count = 0
        for conversation in tuple(self._conversations.values()):
            if conversation.status in {ConversationStatus.QUEUED, ConversationStatus.RUNNING}:
                self.update_conversation_status(
                    conversation.conversation_id,
                    conversation.owner,
                    ConversationStatus.FAILED,
                    failure_message="Workflow interrupted by service restart.",
                )
                count += 1
        return count

    def get_language_preference(self, owner: str) -> str | None:
        return self._language_preferences.get(owner)

    def save_language_preference(self, owner: str, selection: str) -> str:
        self._language_preferences[owner] = selection
        return selection


def create_workflow_catalog() -> WorkflowCatalog:
    return WorkflowCatalog(build_workflow_catalog())
