"""PostgreSQL persistence for Phase 03 conversations and messages."""

from datetime import datetime
from typing import Any

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Conversation,
    ConversationStatus,
    Message,
)
from finmind_agents.serialization import serialize_conversation, serialize_message


class PostgresConversationRepository:
    def __init__(self, dsn: str) -> None:
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for conversation persistence") from exc
        self._psycopg = psycopg
        self._dsn = dsn
        self._ensure_schema()

    def _connect(self) -> Any:
        return self._psycopg.connect(self._dsn, autocommit=True)

    def _ensure_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    data JSONB NOT NULL
                )
                """
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS language_preferences (
                    owner TEXT PRIMARY KEY, selection TEXT NOT NULL
                )"""
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS conversations_owner_updated_idx "
                "ON conversations (owner, updated_at DESC)"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL,
                    data JSONB NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS conversation_messages_order_idx "
                "ON conversation_messages (conversation_id, created_at)"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_series_records (
                    dataset_id TEXT NOT NULL, record_key TEXT NOT NULL,
                    instrument_id TEXT NOT NULL, market_time TIMESTAMPTZ NOT NULL,
                    collected_at TIMESTAMPTZ NOT NULL, source_id TEXT NOT NULL,
                    payload JSONB NOT NULL, PRIMARY KEY (dataset_id, record_key)
                )
                """
            )

    def save_conversation(self, conversation: Conversation) -> None:
        from psycopg.types.json import Json

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, owner, status, updated_at, data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (conversation_id) DO UPDATE SET
                  owner = EXCLUDED.owner, status = EXCLUDED.status,
                  updated_at = EXCLUDED.updated_at, data = EXCLUDED.data
                """,
                (conversation.conversation_id, conversation.owner, conversation.status.value,
                 conversation.updated_at, Json(serialize_conversation(conversation))),
            )

    def get_conversation(self, conversation_id: str, owner: str) -> Conversation | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT owner, data FROM conversations WHERE conversation_id = %s AND owner = %s", (conversation_id, owner))
            row = cursor.fetchone()
        return _restore_conversation(row[1], row[0]) if row else None

    def list_conversations(self, owner: str) -> list[Conversation]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT owner, data FROM conversations WHERE owner = %s ORDER BY updated_at DESC", (owner,))
            rows = cursor.fetchall()
        return [_restore_conversation(row[1], row[0]) for row in rows]

    def update_conversation_status(self, conversation_id: str, owner: str, status: ConversationStatus, *, failure_message: str | None = None) -> Conversation | None:
        from dataclasses import replace
        from finmind_agents.models import utc_now

        current = self.get_conversation(conversation_id, owner)
        if current is None:
            return None
        now = utc_now()
        updated = replace(current, status=status, updated_at=now,
                          completed_at=now if status in {ConversationStatus.SUCCESS, ConversationStatus.FAILED} else None,
                          failure_message=failure_message)
        self.save_conversation(updated)
        return updated

    def save_message(self, message: Message) -> None:
        from psycopg.types.json import Json
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversation_messages (message_id, conversation_id, created_at, data) VALUES (%s, %s, %s, %s)",
                (message.message_id, message.conversation_id, message.created_at, Json(serialize_message(message))),
            )

    def list_messages(self, conversation_id: str, owner: str) -> list[Message]:
        if self.get_conversation(conversation_id, owner) is None:
            return []
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT data FROM conversation_messages WHERE conversation_id = %s ORDER BY created_at", (conversation_id,))
            rows = cursor.fetchall()
        return [_restore_message(row[0]) for row in rows]

    def delete_conversation(self, conversation_id: str, owner: str) -> bool:
        conversation = self.get_conversation(conversation_id, owner)
        if conversation is None or conversation.status not in {ConversationStatus.SUCCESS, ConversationStatus.FAILED}:
            return False
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM conversations WHERE conversation_id = %s AND owner = %s", (conversation_id, owner))
            return cursor.rowcount > 0

    def save_price_series(self, records: tuple[CanonicalMarketDataRecord, ...]) -> None:
        from psycopg.types.json import Json
        with self._connect() as connection, connection.cursor() as cursor:
            for record in records:
                cursor.execute(
                    """INSERT INTO price_series_records (dataset_id, record_key, instrument_id, market_time, collected_at, source_id, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (dataset_id, record_key) DO UPDATE SET instrument_id = EXCLUDED.instrument_id,
                    market_time = EXCLUDED.market_time, collected_at = EXCLUDED.collected_at, source_id = EXCLUDED.source_id, payload = EXCLUDED.payload""",
                    (record.dataset_id, record.record_key, record.instrument_id, record.market_time, record.collected_at, record.source_id, Json(record.payload)),
                )

    def reconcile_interrupted(self) -> int:
        count = 0
        for conversation in self.list_conversations_for_interruption():
            self.update_conversation_status(conversation.conversation_id, conversation.owner, ConversationStatus.FAILED, failure_message="Workflow interrupted by service restart.")
            count += 1
        return count

    def list_conversations_for_interruption(self) -> list[Conversation]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT owner, data FROM conversations WHERE status IN ('queued', 'running')")
            rows = cursor.fetchall()
        return [_restore_conversation(row[1], row[0]) for row in rows]

    def get_language_preference(self, owner: str) -> str | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT selection FROM language_preferences WHERE owner = %s", (owner,))
            row = cursor.fetchone()
        return str(row[0]) if row else None

    def save_language_preference(self, owner: str, selection: str) -> str:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO language_preferences (owner, selection) VALUES (%s, %s)
                ON CONFLICT (owner) DO UPDATE SET selection = EXCLUDED.selection""",
                (owner, selection),
            )
        return selection


def _restore_conversation(data: dict[str, Any], owner: str) -> Conversation:
    return Conversation(
        conversation_id=data["id"], owner=owner, status=ConversationStatus(data["status"]),
        title=data["title"], workflow_id=data.get("workflow_id"), inputs=dict(data.get("inputs") or {}),
        language=data.get("language", "en"), created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        failure_message=data.get("failure_message"),
    )


def _restore_message(data: dict[str, Any]) -> Message:
    from finmind_agents.models import Artifact, Citation, MessageRole, MessageSourceKind
    citations = tuple(
        Citation(
            citation_id=item["citation_id"], record_id=item["record_id"], record_type=item["record_type"],
            source_id=item["source_id"], dataset_id=item["dataset_id"], label=item["label"],
            timestamp=datetime.fromisoformat(item["timestamp"]), instrument_id=item.get("instrument_id"),
            display_content=item.get("display_content"), payload_snapshot=dict(item.get("payload_snapshot") or {}),
            methodology_version=item.get("methodology_version"),
        ) for item in data.get("citations", [])
    )
    artifacts = tuple(
        Artifact(
            artifact_id=item["artifact_id"], artifact_type=item["artifact_type"], title=item["title"],
            inputs=dict(item.get("inputs") or {}), source_refs=tuple(item.get("source_refs") or ()),
            status=item.get("status", "ready"), reason=item.get("reason"), file_type=item.get("file_type"),
            file=item.get("file"), mime_type=item.get("mime_type"), chart_intent=item.get("chart_intent"),
            spec=item.get("spec"), downloads=tuple(item.get("downloads") or ()),
        ) for item in data.get("artifacts", [])
    )
    return Message(message_id=data["id"], conversation_id=data.get("conversation_id", ""),
                   role=MessageRole(data["role"]), source_kind=MessageSourceKind(data["source_kind"]),
                   content=data["content"], created_at=datetime.fromisoformat(data["created_at"]),
                   citations=citations, artifacts=artifacts, workflow_id=data.get("workflow_id"))
