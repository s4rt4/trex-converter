from pathlib import Path

from app.core.task import Task, TaskStatus


def test_task_defaults_to_empty_extra_inputs() -> None:
    task = Task(
        input_path=Path("a.pdf"),
        output_path=Path("out.pdf"),
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
    )

    assert task.extra_inputs == []
    assert task.inputs == [Path("a.pdf")]
    assert task.formats_in == ["pdf"]


def test_task_inputs_property_concatenates_primary_and_extras() -> None:
    task = Task(
        input_path=Path("a.pdf"),
        output_path=Path("merged.pdf"),
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        extra_inputs=[Path("b.pdf"), Path("c.pdf")],
    )

    assert task.inputs == [Path("a.pdf"), Path("b.pdf"), Path("c.pdf")]
    assert task.formats_in == ["pdf", "pdf", "pdf"]


def test_task_post_init_coerces_extras_to_path() -> None:
    task = Task(
        input_path="a.pdf",
        output_path="m.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        extra_inputs=["b.pdf", "c.pdf"],
    )

    assert all(isinstance(p, Path) for p in task.extra_inputs)
    assert all(isinstance(p, Path) for p in task.inputs)


def test_task_formats_in_derives_suffix_per_extra() -> None:
    task = Task(
        input_path=Path("clip.mp4"),
        output_path=Path("out.mp4"),
        format_in="mp4",
        format_out="mp4",
        engine="ffmpeg",
        extra_inputs=[Path("clip2.MOV"), Path("clip3.webm")],
    )

    # Primary format is normalized in __post_init__; extras are derived from suffix
    assert task.formats_in == ["mp4", "mov", "webm"]


def test_from_paths_accepts_extra_inputs() -> None:
    task = Task.from_paths(
        input_path=Path("a.pdf"),
        output_path=Path("merged.pdf"),
        engine="pdf",
        extra_inputs=[Path("b.pdf")],
    )

    assert task.extra_inputs == [Path("b.pdf")]
    assert task.format_in == "pdf"
    assert task.format_out == "pdf"


def test_existing_single_input_api_unchanged() -> None:
    # Backward-compat regression: pre-refactor callers that don't touch
    # extra_inputs should keep working without surprises.
    task = Task(
        input_path=Path("input.png"),
        output_path=Path("output.webp"),
        format_in="png",
        format_out="webp",
        engine="imagemagick",
    )

    assert task.input_path == Path("input.png")
    assert task.format_in == "png"
    assert task.extra_inputs == []
    assert task.status == TaskStatus.PENDING
