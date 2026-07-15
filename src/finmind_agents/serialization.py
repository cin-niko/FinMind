from typing import Any

from finmind_agents.models import (
    Artifact,
    Citation,
    Conversation,
    Message,
    WorkflowResult,
)


def serialize_citation(citation: Citation) -> dict[str, Any]:
    return {
        "citation_id": citation.citation_id,
        "record_id": citation.record_id,
        "record_type": citation.record_type,
        "source_id": citation.source_id,
        "dataset_id": citation.dataset_id,
        "label": citation.label,
        "timestamp": citation.timestamp.isoformat(),
        "instrument_id": citation.instrument_id,
        "display_content": citation.display_content,
        "payload_snapshot": citation.payload_snapshot,
        "methodology_version": citation.methodology_version,
    }


def serialize_artifact(artifact: Artifact) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "title": artifact.title,
        "inputs": artifact.inputs,
        "source_refs": list(artifact.source_refs),
        "status": artifact.status,
        "downloads": list(artifact.downloads),
    }
    for key in ("reason", "file_type", "file", "mime_type", "chart_intent", "spec"):
        value = getattr(artifact, key)
        if value is not None:
            payload[key] = value
    return payload


def serialize_workflow_result(result: WorkflowResult) -> dict[str, Any]:
    return {
        "workflow_id": result.workflow_id,
        "inputs": result.inputs,
        "sections": list(result.sections),
        "steps": list(result.steps),
        "collection": result.collection,
        "citations": [serialize_citation(item) for item in result.citations],
        "artifacts": [serialize_artifact(item) for item in result.artifacts],
        "grounding": result.grounding,
        "language": result.language,
    }


def serialize_message(message: Message) -> dict[str, Any]:
    return {
        "id": message.message_id,
        "conversation_id": message.conversation_id,
        "role": message.role.value,
        "source_kind": message.source_kind.value,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "workflow_id": message.workflow_id,
        "citations": [serialize_citation(item) for item in message.citations],
        "artifacts": [serialize_artifact(item) for item in message.artifacts],
        "workflow_result": (
            serialize_workflow_result(message.workflow_result)
            if message.workflow_result is not None
            else None
        ),
    }


def serialize_conversation(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": conversation.conversation_id,
        "title": conversation.title,
        "status": conversation.status.value,
        "workflow_id": conversation.workflow_id,
        "inputs": conversation.inputs,
        "language": conversation.language,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "completed_at": (
            conversation.completed_at.isoformat()
            if conversation.completed_at is not None
            else None
        ),
        "failure_message": conversation.failure_message,
    }
