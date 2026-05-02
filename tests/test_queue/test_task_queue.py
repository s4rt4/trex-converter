from pathlib import Path
import asyncio

import pytest

from app.core.queue import TaskQueue
from app.core.task import Task, TaskStatus
from app.engines.base import BaseEngine, EngineCapabilities, StubEngine


def make_task() -> Task:
    return Task(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp3"),
        format_in="mp4",
        format_out="mp3",
        engine="ffmpeg",
    )


@pytest.mark.asyncio
async def test_queue_runs_task_to_success() -> None:
    engine = StubEngine("ffmpeg", {("mp4", "mp3")}, "ffmpeg")
    queue = TaskQueue(lambda _format_in, _format_out: engine)
    task = make_task()

    queue.add(task)
    await queue.wait_idle()

    assert task.status == TaskStatus.SUCCESS
    assert task.progress == 1.0
    assert "Task completed" in task.log
    await queue.close()


@pytest.mark.asyncio
async def test_retry_failed_task_requeues() -> None:
    class FailingEngine(StubEngine):
        async def convert(self, task: Task) -> None:
            raise RuntimeError("boom")

    queue = TaskQueue(lambda _format_in, _format_out: FailingEngine("ffmpeg", {("mp4", "mp3")}, "ffmpeg"))
    task = make_task()

    queue.add(task)
    await queue.wait_idle()
    assert task.status == TaskStatus.FAILED

    queue.retry(task.id)
    await queue.wait_idle()

    assert task.status == TaskStatus.FAILED
    assert task.retries == 1
    await queue.close()


@pytest.mark.asyncio
async def test_cancel_running_task_calls_engine_cancel() -> None:
    class SlowEngine(BaseEngine):
        name = "slow"

        def __init__(self) -> None:
            self.cancel_called = False

        async def convert(self, task: Task) -> None:
            await asyncio.sleep(10)

        async def cancel(self, task: Task) -> None:
            self.cancel_called = True
            task.mark_cancelled()

        def supports(self, format_in: str, format_out: str) -> bool:
            return True

        @property
        def capabilities(self) -> EngineCapabilities:
            return EngineCapabilities(True, True, "slow")

    engine = SlowEngine()
    queue = TaskQueue(lambda _format_in, _format_out: engine)
    task = make_task()

    queue.add(task)
    while task.status != TaskStatus.RUNNING:
        await asyncio.sleep(0.01)
    queue.cancel(task.id)
    await queue.wait_idle()

    assert task.status == TaskStatus.CANCELLED
    assert engine.cancel_called is True
    await queue.close()
