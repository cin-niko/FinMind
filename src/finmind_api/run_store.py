"""Run persistence for the backend API layer.

The agentic layer (`finmind_agents`) only declares the `RunRepository` contract
and hands finished `ExecutionRun` records to it. The concrete persistence
implementation lives here in the API layer so the agentic runtime stays free of
storage/infrastructure concerns.
"""

from datetime import datetime
from typing import Any

from finmind_agents.models import ExecutionRun, RunStatus


def persist_run(run: ExecutionRun) -> dict[str, Any]:
    """Full run record for storage (includes requested_by)."""
    return {
        "run_id": run.run_id,
        "kind": run.kind,
        "status": run.status.value,
        "requested_by": run.requested_by,
        "inputs": run.inputs,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "output": run.output,
        "logs": run.logs,
        "title": run.title,
    }


def restore_run(data: dict[str, Any]) -> ExecutionRun:
    started_at = datetime.fromisoformat(data["started_at"])
    completed_at = (
        datetime.fromisoformat(data["completed_at"])
        if data.get("completed_at")
        else None
    )
    return ExecutionRun(
        run_id=data["run_id"],
        kind=data["kind"],
        status=RunStatus(data["status"]),
        requested_by=data["requested_by"],
        inputs=dict(data.get("inputs") or {}),
        started_at=started_at,
        completed_at=completed_at,
        output=dict(data.get("output") or {}),
        logs=list(data.get("logs") or []),
        title=data.get("title"),
    )


class PostgresRunRepository:
    """Run store backed by PostgreSQL.

    One row per run; the full run record is stored as JSONB in ``data`` so
    workflow and chat runs share one table via the ``kind`` discriminator.
    ``run_id`` is the primary key and ``started_at`` backs history ordering. The
    schema is bootstrapped idempotently on init.
    """

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:  # pragma: no cover - dependency-guarded
            raise RuntimeError(
                "psycopg is required for the Postgres run store; "
                "add 'psycopg[binary]' to the project dependencies"
            ) from exc
        self._dsn = dsn
        self._psycopg = psycopg
        self._ensure_schema()

    def _connect(self) -> Any:
        return self._psycopg.connect(self._dsn, autocommit=True)

    def _ensure_schema(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id        TEXT PRIMARY KEY,
                    kind          TEXT NOT NULL,
                    status        TEXT NOT NULL,
                    requested_by  TEXT NOT NULL,
                    started_at    TIMESTAMPTZ NOT NULL,
                    completed_at  TIMESTAMPTZ,
                    data          JSONB NOT NULL
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS runs_started_at_idx "
                "ON runs (started_at DESC)"
            )

    def save(self, run: ExecutionRun) -> None:
        from psycopg.types.json import Json

        data = persist_run(run)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs
                    (run_id, kind, status, requested_by, started_at,
                     completed_at, data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    kind         = EXCLUDED.kind,
                    status       = EXCLUDED.status,
                    requested_by = EXCLUDED.requested_by,
                    started_at   = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    data         = EXCLUDED.data
                """,
                (
                    run.run_id,
                    run.kind,
                    run.status.value,
                    run.requested_by,
                    run.started_at,
                    run.completed_at,
                    Json(data),
                ),
            )

    def get(self, run_id: str) -> ExecutionRun | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT data FROM runs WHERE run_id = %s", (run_id,))
            row = cur.fetchone()
        if row is None:
            return None
        return restore_run(row[0])

    def list(self) -> list[ExecutionRun]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT data FROM runs ORDER BY started_at DESC")
            rows = cur.fetchall()
        return [restore_run(row[0]) for row in rows]

    def delete(self, run_id: str) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM runs WHERE run_id = %s", (run_id,))
            return cur.rowcount > 0

    def update_title(self, run_id: str, title: str) -> ExecutionRun | None:
        from psycopg.types.json import Json

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT data FROM runs WHERE run_id = %s", (run_id,))
            row = cur.fetchone()
            if row is None:
                return None
            data = row[0]
            data["title"] = title
            cur.execute(
                "UPDATE runs SET data = %s WHERE run_id = %s",
                (Json(data), run_id),
            )
        return restore_run(data)
