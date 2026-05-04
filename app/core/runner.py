from __future__ import annotations

from app.core.queue import TaskQueue
from app.core.registry import ConversionRegistry
from app.data.database import TaskRepository


def create_default_queue(max_concurrency: int = 2, persistent: bool = True) -> TaskQueue:
    registry = ConversionRegistry()
    repository = TaskRepository() if persistent else None
    return TaskQueue(
        registry.resolve,
        max_concurrency=max_concurrency,
        repository=repository,
        resume_pending=persistent,
        engine_by_name=registry.engine_by_name,
    )
