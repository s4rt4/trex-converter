from __future__ import annotations

import json
from pathlib import Path
from sqlite3 import Row

from app.core.task import Task, TaskStatus


def task_to_record(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "input_path": str(task.input_path),
        "output_path": str(task.output_path),
        "format_in": task.format_in,
        "format_out": task.format_out,
        "engine": task.engine,
        "options": json.dumps(task.options),
        "status": task.status.value,
        "progress": task.progress,
        "log": json.dumps(task.log),
        "error": task.error,
        "retries": task.retries,
        "max_retries": task.max_retries,
        "extra_inputs": json.dumps([str(p) for p in task.extra_inputs]),
    }


def task_from_row(row: Row) -> Task:
    extra_inputs_raw = _row_get(row, "extra_inputs") or "[]"
    try:
        extra_inputs = [Path(p) for p in json.loads(extra_inputs_raw)]
    except (TypeError, ValueError):
        extra_inputs = []
    return Task(
        id=row["id"],
        input_path=Path(row["input_path"]),
        output_path=Path(row["output_path"]),
        format_in=row["format_in"],
        format_out=row["format_out"],
        engine=row["engine"],
        options=json.loads(row["options"] or "{}"),
        status=TaskStatus(row["status"]),
        progress=float(row["progress"]),
        log=json.loads(row["log"] or "[]"),
        error=row["error"],
        retries=int(row["retries"]),
        max_retries=int(row["max_retries"]),
        extra_inputs=extra_inputs,
    )


def _row_get(row: Row, key: str) -> object | None:
    try:
        return row[key]
    except (IndexError, KeyError):
        return None
