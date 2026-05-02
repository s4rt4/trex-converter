from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.core.task import Task, TaskStatus
from app.data.database import TaskRepository
from app.engines.base import BaseEngine

TaskEventCallback = Callable[[Task], None | Awaitable[None]]
EngineResolver = Callable[[str, str], BaseEngine]


class TaskQueue:
    def __init__(
        self,
        engine_resolver: EngineResolver,
        max_concurrency: int = 2,
        repository: TaskRepository | None = None,
        resume_pending: bool = False,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self._engine_resolver = engine_resolver
        self._max_concurrency = max_concurrency
        self._tasks: dict[str, Task] = {}
        self._pending: asyncio.Queue[str] = asyncio.Queue()
        self._running: dict[str, asyncio.Task[None]] = {}
        self._running_engines: dict[str, BaseEngine] = {}
        self._repository = repository
        self._callbacks: list[TaskEventCallback] = []
        self._dispatcher: asyncio.Task[None] | None = None
        self._closed = False
        if self._repository:
            for task in self._repository.list():
                self._tasks[task.id] = task
            if resume_pending:
                for task in self._repository.pending_for_resume():
                    self._tasks[task.id] = task
                    self._pending.put_nowait(task.id)

    @property
    def max_concurrency(self) -> int:
        return self._max_concurrency

    def subscribe(self, callback: TaskEventCallback) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if not self._pending.empty():
            self._ensure_dispatcher()

    def add(self, task: Task) -> Task:
        if self._closed:
            raise RuntimeError("TaskQueue is closed")
        if task.id in self._tasks:
            raise ValueError(f"Task already exists: {task.id}")
        self._tasks[task.id] = task
        self._persist(task)
        self._pending.put_nowait(task.id)
        self._ensure_dispatcher()
        self._emit_nowait(task)
        return task

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def all(self) -> list[Task]:
        return list(self._tasks.values())

    def cancel(self, task_id: str) -> None:
        task = self.get(task_id)
        if task.status == TaskStatus.RUNNING:
            running_task = self._running.get(task_id)
            if running_task:
                running_task.cancel()
        elif task.status == TaskStatus.PENDING:
            task.mark_cancelled()
            self._persist(task)
            self._emit_nowait(task)

    def retry(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.reset_for_retry()
        self._persist(task)
        self._pending.put_nowait(task.id)
        self._ensure_dispatcher()
        self._emit_nowait(task)
        return task

    async def wait_idle(self) -> None:
        while not self._pending.empty() or self._running:
            await asyncio.sleep(0.01)

    async def close(self) -> None:
        self._closed = True
        for worker in list(self._running.values()):
            worker.cancel()
        await asyncio.gather(*self._running.values(), return_exceptions=True)
        if self._dispatcher:
            self._dispatcher.cancel()
            await asyncio.gather(self._dispatcher, return_exceptions=True)

    def _ensure_dispatcher(self) -> None:
        if self._dispatcher is None or self._dispatcher.done():
            self._dispatcher = asyncio.create_task(self._dispatch())

    async def _dispatch(self) -> None:
        while not self._closed:
            task_id = await self._pending.get()
            task = self._tasks[task_id]
            if task.status != TaskStatus.PENDING:
                self._pending.task_done()
                continue

            while len(self._running) >= self._max_concurrency:
                await asyncio.sleep(0.01)

            worker = asyncio.create_task(self._run_task(task))
            self._running[task.id] = worker
            worker.add_done_callback(
                lambda _, task_id=task.id: self._running.pop(task_id, None)
            )
            self._pending.task_done()

    async def _run_task(self, task: Task) -> None:
        try:
            engine = self._engine_resolver(task.format_in, task.format_out)
            self._running_engines[task.id] = engine
            task.mark_running()
            self._persist(task)
            await self._emit(task)
            await engine.convert(task)
            if task.status != TaskStatus.CANCELLED:
                task.mark_success()
        except asyncio.CancelledError:
            engine = self._running_engines.get(task.id)
            if engine:
                await engine.cancel(task)
            else:
                task.mark_cancelled()
        except Exception as exc:
            task.mark_failed(str(exc))
        finally:
            self._running_engines.pop(task.id, None)
            self._persist(task)
            await self._emit(task)

    async def _emit(self, task: Task) -> None:
        for callback in self._callbacks:
            result = callback(task)
            if result is not None:
                await result

    def _emit_nowait(self, task: Task) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._emit(task))

    def _persist(self, task: Task) -> None:
        if self._repository:
            self._repository.save(task)
