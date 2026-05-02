from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.task import Task, TaskStatus
from app.data.models import task_from_row, task_to_record
from app.utils.paths import config_dir


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    input_path TEXT NOT NULL,
    output_path TEXT NOT NULL,
    format_in TEXT NOT NULL,
    format_out TEXT NOT NULL,
    engine TEXT NOT NULL,
    options TEXT NOT NULL,
    status TEXT NOT NULL,
    progress REAL NOT NULL,
    log TEXT NOT NULL,
    error TEXT,
    retries INTEGER NOT NULL,
    max_retries INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at);
"""


class TaskRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def save(self, task: Task) -> None:
        record = task_to_record(task)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, input_path, output_path, format_in, format_out, engine,
                    options, status, progress, log, error, retries, max_retries
                )
                VALUES (
                    :id, :input_path, :output_path, :format_in, :format_out,
                    :engine, :options, :status, :progress, :log, :error,
                    :retries, :max_retries
                )
                ON CONFLICT(id) DO UPDATE SET
                    input_path = excluded.input_path,
                    output_path = excluded.output_path,
                    format_in = excluded.format_in,
                    format_out = excluded.format_out,
                    engine = excluded.engine,
                    options = excluded.options,
                    status = excluded.status,
                    progress = excluded.progress,
                    log = excluded.log,
                    error = excluded.error,
                    retries = excluded.retries,
                    max_retries = excluded.max_retries,
                    updated_at = CURRENT_TIMESTAMP
                """,
                record,
            )

    def list(self, status: TaskStatus | None = None) -> list[Task]:
        with self._connect() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM tasks ORDER BY updated_at DESC, created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC, created_at DESC",
                    (status.value,),
                ).fetchall()
        return [task_from_row(row) for row in rows]

    def get(self, task_id: str) -> Task | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return task_from_row(row) if row else None

    def pending_for_resume(self) -> list[Task]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
                """,
                (TaskStatus.PENDING.value, TaskStatus.RUNNING.value),
            ).fetchall()
        tasks = [task_from_row(row) for row in rows]
        for task in tasks:
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PENDING
                task.append_log("Recovered pending task after application restart")
                self.save(task)
        return tasks

    def _migrate(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection


def default_db_path() -> Path:
    return config_dir() / "tasks.sqlite3"
