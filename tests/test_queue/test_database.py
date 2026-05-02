from pathlib import Path

from app.core.task import Task, TaskStatus
from app.data.database import TaskRepository


def test_task_repository_saves_and_loads_task(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "tasks.sqlite3")
    task = Task(
        input_path=Path("input.png"),
        output_path=Path("output.webp"),
        format_in="png",
        format_out="webp",
        engine="imagemagick",
        options={"quality": 80},
    )
    task.mark_running()
    task.progress = 0.4

    repository.save(task)
    loaded = repository.get(task.id)

    assert loaded is not None
    assert loaded.id == task.id
    assert loaded.options == {"quality": 80}
    assert loaded.status == TaskStatus.RUNNING
    assert loaded.progress == 0.4


def test_task_repository_recovers_running_tasks_as_pending(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "tasks.sqlite3")
    task = Task(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp3"),
        format_in="mp4",
        format_out="mp3",
        engine="ffmpeg",
    )
    task.mark_running()
    repository.save(task)

    recovered = repository.pending_for_resume()

    assert len(recovered) == 1
    assert recovered[0].status == TaskStatus.PENDING
    assert repository.get(task.id).status == TaskStatus.PENDING
