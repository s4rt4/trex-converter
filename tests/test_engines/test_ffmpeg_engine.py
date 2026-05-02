from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.ffmpeg_engine import FFmpegEngine


@pytest.mark.asyncio
async def test_ffmpeg_engine_runs_subprocess_and_updates_progress(tmp_path, monkeypatch) -> None:
    fake_ffmpeg = tmp_path / "ffmpeg"
    fake_ffmpeg.write_text(
        "#!/bin/sh\n"
        "echo 'Duration: 00:00:10.00, start: 0.000000' >&2\n"
        "echo 'out_time_ms=5000000' >&2\n"
        "echo 'progress=end' >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ffmpeg.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    task = Task(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp3"),
        format_in="mp4",
        format_out="mp3",
        engine="ffmpeg",
        options={"bitrate": "192k"},
    )

    await FFmpegEngine().convert(task)

    assert task.progress == 1.0
    assert any("Running: ffmpeg" in line for line in task.log)
