import sqlite3
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


def test_task_repository_persists_extra_inputs(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "tasks.sqlite3")
    task = Task(
        input_path=Path("a.pdf"),
        output_path=Path("merged.pdf"),
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "merge"},
        extra_inputs=[Path("b.pdf"), Path("c.pdf")],
    )
    repository.save(task)
    loaded = repository.get(task.id)

    assert loaded is not None
    assert [str(p) for p in loaded.extra_inputs] == ["b.pdf", "c.pdf"]
    assert [str(p) for p in loaded.inputs] == ["a.pdf", "b.pdf", "c.pdf"]


def test_repository_migrates_legacy_db_without_extra_inputs_column(tmp_path) -> None:
    db_path = tmp_path / "legacy.sqlite3"
    # Create a pre-extra_inputs schema by hand and seed one row.
    legacy_schema = """
        CREATE TABLE tasks (
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
        )
    """
    with sqlite3.connect(db_path) as connection:
        connection.executescript(legacy_schema)
        connection.execute(
            """
            INSERT INTO tasks (
                id, input_path, output_path, format_in, format_out, engine,
                options, status, progress, log, error, retries, max_retries
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-1",
                "in.png",
                "out.webp",
                "png",
                "webp",
                "imagemagick",
                "{}",
                "success",
                1.0,
                "[]",
                None,
                0,
                2,
            ),
        )

    repository = TaskRepository(db_path)
    legacy = repository.get("legacy-1")

    assert legacy is not None
    assert legacy.extra_inputs == []  # column added with default '[]'

    # New saves can now include extras without schema errors.
    task = Task(
        input_path=Path("a.pdf"),
        output_path=Path("m.pdf"),
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        extra_inputs=[Path("b.pdf")],
    )
    repository.save(task)
    loaded = repository.get(task.id)
    assert loaded is not None
    assert [str(p) for p in loaded.extra_inputs] == ["b.pdf"]
