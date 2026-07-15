"""Conversation adapter for workflow results.

This module deliberately owns the workflow-to-message boundary.  Workflows
produce transient ``WorkflowResult`` values; only this adapter persists a
user-visible assistant message.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from finmind_agents.models import (
    Conversation,
    ConversationStatus,
    WorkflowResult,
    utc_now,
)
from finmind_agents.repositories import ConversationRepository
from finmind_agents.serialization import (
    serialize_conversation,
    serialize_message,
    serialize_workflow_result,
)
from finmind_agents.streaming.models import StreamEventKind
from finmind_agents.workflows.service import WorkflowService
from finmind_agents.workflows.conversation_adapter import ConversationAdapter


@dataclass(frozen=True)
class ConversationStreamEvent:
    event_id: str
    conversation_id: str
    sequence: int
    kind: str
    created_at: str
    payload: dict[str, object]

    @property
    def event_name(self) -> str:
        return self.kind

    def to_payload(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "conversation_id": self.conversation_id,
            "sequence": self.sequence,
            "kind": self.kind,
            "created_at": self.created_at,
            "payload": self.payload,
        }


class ConversationWorkflowService:
    def __init__(
        self,
        workflows: WorkflowService,
        conversations: ConversationRepository,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._workflows = workflows
        self._conversations = conversations
        self._timeout_seconds = timeout_seconds
        self._streams: dict[str, asyncio.Queue[ConversationStreamEvent | None]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._adapter = ConversationAdapter()

    def start(
        self,
        workflow_id: str,
        inputs: dict[str, object],
        owner: str,
        language: str,
    ) -> Conversation:
        prepared = self._workflows.prepare_workflow_run(workflow_id, inputs, language)
        now = utc_now()
        conversation = Conversation(
            conversation_id=f"conv_{uuid4().hex[:12]}",
            owner=owner,
            status=ConversationStatus.QUEUED,
            title=prepared.workflow.title,
            workflow_id=workflow_id,
            inputs=prepared.run_inputs,
            language=prepared.language,
            created_at=now,
            updated_at=now,
        )
        self._conversations.save_conversation(conversation)
        queue: asyncio.Queue[ConversationStreamEvent | None] = asyncio.Queue()
        self._streams[conversation.conversation_id] = queue
        self._tasks[conversation.conversation_id] = asyncio.create_task(
            self._execute(conversation, prepared.run_inputs),
            name=f"finmind-workflow-{conversation.conversation_id}",
        )
        return conversation

    async def events(self, conversation_id: str) -> AsyncIterator[ConversationStreamEvent]:
        queue = self._streams.get(conversation_id)
        if queue is None:
            return
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

    def list(self, owner: str) -> list[dict[str, object]]:
        return [serialize_conversation(item) for item in self._conversations.list_conversations(owner)]

    def get(self, conversation_id: str, owner: str) -> dict[str, object] | None:
        conversation = self._conversations.get_conversation(conversation_id, owner)
        if conversation is None:
            return None
        payload = serialize_conversation(conversation)
        payload["messages"] = [
            serialize_message(message)
            for message in self._conversations.list_messages(conversation_id, owner)
        ]
        return payload

    def delete(self, conversation_id: str, owner: str) -> bool:
        return self._conversations.delete_conversation(conversation_id, owner)

    async def _execute(self, conversation: Conversation, inputs: dict[str, object]) -> None:
        sequence = 0

        async def emit(kind: str, payload: dict[str, object]) -> None:
            nonlocal sequence
            sequence += 1
            await self._streams[conversation.conversation_id].put(
                ConversationStreamEvent(
                    event_id=f"evt_{sequence:04d}",
                    conversation_id=conversation.conversation_id,
                    sequence=sequence,
                    kind=kind,
                    created_at=utc_now().isoformat(),
                    payload=payload,
                )
            )

        self._conversations.update_conversation_status(
            conversation.conversation_id,
            conversation.owner,
            ConversationStatus.RUNNING,
        )
        await emit("conversation.started", {"conversation": serialize_conversation(conversation)})
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async for event in self._workflows.stream_workflow(
                    conversation.workflow_id or "",
                    inputs,
                    conversation.owner,
                    conversation.language,
                ):
                    if event.kind == StreamEventKind.WORKFLOW_STAGE:
                        await emit("conversation.stage", event.payload)
                    elif event.kind == StreamEventKind.MESSAGE_DELTA:
                        await emit("message.delta", event.payload)
                    elif event.kind == StreamEventKind.CITATION:
                        await emit("citation", event.payload)
                    elif event.kind == StreamEventKind.ARTIFACT:
                        await emit("artifact", event.payload)
                    elif event.kind == StreamEventKind.WORKFLOW_COMPLETED:
                        result = event.payload["result"]
                        if not isinstance(result, WorkflowResult):
                            raise RuntimeError("Workflow completed without a workflow result")
                        message = self._adapter.to_first_assistant_message(conversation, result)
                        self._conversations.save_message(message)
                        saved = self._conversations.update_conversation_status(
                            conversation.conversation_id,
                            conversation.owner,
                            ConversationStatus.SUCCESS,
                        )
                        await emit("message.created", {"message": serialize_message(message)})
                        await emit(
                            "conversation.completed",
                            {
                                "conversation": serialize_conversation(saved or conversation),
                                "message": serialize_message(message),
                                "result": serialize_workflow_result(result),
                            },
                        )
                    elif event.kind == StreamEventKind.WORKFLOW_FAILED:
                        raise RuntimeError(_safe_failure_message(event.payload.get("message")))
        except TimeoutError:
            await self._fail(
                conversation,
                emit,
                _localized_failure_message(conversation.language, "timeout"),
            )
        except Exception:
            await self._fail(
                conversation,
                emit,
                _localized_failure_message(conversation.language, "failed"),
            )
        finally:
            await self._streams[conversation.conversation_id].put(None)
            self._tasks.pop(conversation.conversation_id, None)

    async def _fail(
        self,
        conversation: Conversation,
        emit: Any,
        message: str,
    ) -> None:
        saved = self._conversations.update_conversation_status(
            conversation.conversation_id,
            conversation.owner,
            ConversationStatus.FAILED,
            failure_message=message,
        )
        await emit(
            "conversation.failed",
            {"conversation": serialize_conversation(saved or conversation), "message": message},
        )


def _safe_failure_message(value: object) -> str:
    return str(value) if isinstance(value, str) and value else "Workflow could not be completed."


def _localized_failure_message(language: str, kind: str) -> str:
    messages = {
        "en": {
            "timeout": "Workflow timed out after 120 seconds.",
            "failed": "Workflow could not be completed. Please try again.",
        },
        "vi": {
            "timeout": "Quy trình đã hết thời gian chờ sau 120 giây.",
            "failed": "Không thể hoàn tất quy trình. Vui lòng thử lại.",
        },
    }
    return messages.get(language, messages["en"]).get(kind, messages["en"]["failed"])
