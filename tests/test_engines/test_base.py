from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.ffmpeg_engine import FFmpegEngine, _parse_duration, _parse_progress


@pytest.mark.asyncio
async def test_stub_engine_marks_progress_and_supports_registered_pair() -> None:
    engine = FFmpegEngine()
    task = Task(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp3"),
        format_in="mp4",
        format_out="mp3",
        engine=engine.name,
    )

    assert engine.supports("mp4", "mp3")
    assert engine.capabilities.supports_progress is True
    assert task.progress == 0.0


def test_ffmpeg_progress_parsing() -> None:
    duration = _parse_duration("  Duration: 00:01:40.00, start: 0.000000")

    assert duration == 100.0
    assert _parse_progress("out_time_ms=50000000", duration) == 0.5
    assert _parse_progress("progress=end", duration) == 1.0
