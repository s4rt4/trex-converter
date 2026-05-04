from __future__ import annotations

from app.core.queue import TaskQueue
from app.core.registry import ConversionRegistry
from app.core.settings import get_settings
from app.data.database import TaskRepository


def create_default_queue(
    max_concurrency: int | None = None,
    persistent: bool = True,
) -> TaskQueue:
    registry = ConversionRegistry()
    repository = TaskRepository() if persistent else None
    if max_concurrency is None:
        max_concurrency = max(1, get_settings().max_concurrency)
    return TaskQueue(
        registry.resolve,
        max_concurrency=max_concurrency,
        repository=repository,
        resume_pending=persistent,
        engine_by_name=registry.engine_by_name,
    )
