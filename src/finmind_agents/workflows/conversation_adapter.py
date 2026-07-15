"""Deterministic conversion of transient workflow output into an assistant message."""

from uuid import uuid4

from finmind_agents.models import (
    Conversation,
    Message,
    MessageRole,
    MessageSourceKind,
    WorkflowResult,
    utc_now,
)


class ConversationAdapter:
    def to_first_assistant_message(
        self,
        conversation: Conversation,
        result: WorkflowResult,
    ) -> Message:
        content = "\n\n".join(
            str(section.get("content", "")).strip()
            for section in result.sections
            if str(section.get("content", "")).strip()
        ) or "Unavailable"
        return Message(
            message_id=f"msg_{uuid4().hex[:12]}",
            conversation_id=conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            source_kind=MessageSourceKind.WORKFLOW,
            content=content,
            created_at=utc_now(),
            citations=result.citations,
            artifacts=result.artifacts,
            workflow_id=result.workflow_id,
            workflow_result=result,
        )
