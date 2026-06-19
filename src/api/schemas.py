from typing import Any

from pydantic import BaseModel

from api.platform.models import ExecutionRun


class LoginRequest(BaseModel):
    username: str
    password: str


def serialize_run(run: ExecutionRun) -> dict[str, Any]:
    return {
        "id": run.run_id,
        "kind": run.kind,
        "status": run.status.value,
        "inputs": run.inputs,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "output": run.output,
        "logs": run.logs,
    }
