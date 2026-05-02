from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import uuid4


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Task:
    input_path: Path
    output_path: Path
    format_in: str
    format_out: str
    engine: str
    options: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    log: list[str] = field(default_factory=list)
    error: str | None = None
    retries: int = 0
    max_retries: int = 2

    def __post_init__(self) -> None:
        self.input_path = Path(self.input_path)
        self.output_path = Path(self.output_path)
        self.format_in = self.format_in.lower().lstrip(".")
        self.format_out = self.format_out.lower().lstrip(".")
        self.progress = max(0.0, min(1.0, self.progress))

    @classmethod
    def from_paths(
        cls,
        input_path: Path,
        output_path: Path,
        engine: str,
        options: dict | None = None,
    ) -> "Task":
        return cls(
            input_path=input_path,
            output_path=output_path,
            format_in=Path(input_path).suffix.lstrip("."),
            format_out=Path(output_path).suffix.lstrip("."),
            engine=engine,
            options=options or {},
        )

    def append_log(self, message: str) -> None:
        self.log.append(message)

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.error = None
        self.append_log("Task started")

    def mark_success(self) -> None:
        self.status = TaskStatus.SUCCESS
        self.progress = 1.0
        self.error = None
        self.append_log("Task completed")

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error
        self.append_log(f"Task failed: {error}")

    def mark_cancelled(self) -> None:
        self.status = TaskStatus.CANCELLED
        self.append_log("Task cancelled")

    def can_retry(self) -> bool:
        return self.status == TaskStatus.FAILED and self.retries < self.max_retries

    def reset_for_retry(self) -> None:
        if not self.can_retry():
            raise ValueError("Task cannot be retried")
        self.retries += 1
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.error = None
        self.append_log(f"Retry queued ({self.retries}/{self.max_retries})")
